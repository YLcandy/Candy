import os
import requests
from playwright.sync_api import sync_playwright

STORE_URL = "https://store.eternalhero.rivvy.games/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

def send_discord(message, image_path=None):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL이 설정되지 않아 디스코드 알림을 건너뜁니다.")
        return
    try:
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img:
                requests.post(
                    DISCORD_WEBHOOK_URL,
                    data={"content": message},
                    files={"file": (os.path.basename(image_path), img, "image/png")},
                    timeout=15,
                )
        else:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=15)
    except Exception as e:
        print("디스코드 전송 실패:", e)

def load_players():
    players = []
    if os.path.exists("players.txt"):
        with open("players.txt", "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                if "#" in raw:
                    pid, memo = raw.split("#", 1)
                    pid = pid.strip()
                    memo = memo.strip()
                else:
                    pid, memo = raw, ""
                if pid:
                    players.append((pid, memo))

    if not players:
        raw_ids = os.environ.get("PLAYER_ID", "")
        for pid in raw_ids.replace(",", "\n").splitlines():
            if pid.strip():
                players.append((pid.strip(), ""))

    return players

def claim_for_player(browser, idx, player_id, memo):
    label = f"{idx}번 계정 ({memo})" if memo else f"{idx}번 계정"
    print(f"\n--- [{label}] 수령 시작 ---")
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    screenshot_path = f"result_{idx}.png"
    logs = []
    claimed_count = 0
    already_count = 0
    has_error = False

    try:
        # 1. 웹 상점 사이트로 이동
        page.goto(STORE_URL, wait_until="networkidle")
        page.wait_for_timeout(1500)

        # 2. 쿠키 안내 팝업 닫기
        dismiss_btn = page.get_by_role("button", name="Dismiss")
        if dismiss_btn.is_visible():
            dismiss_btn.click()
            page.wait_for_timeout(500)

        # 3. 'Enter your player id...' 입력창에 타이핑
        inp = page.get_by_placeholder("Enter your player id...")
        inp.click()
        inp.press_sequentially(player_id, delay=50)
        page.wait_for_timeout(500)

        # 4. 입력창과 한 세트인 'Log in' 버튼 클릭
        login_box = inp.locator("xpath=ancestor::*[.//button[contains(., 'Log in')]][1]")
        login_box.get_by_role("button", name="Log in").click()

        # 5. 로그인 완료 대기
        inp.wait_for(state="hidden", timeout=15000)
        print(f"[{label}] 로그인 성공!")
        page.wait_for_timeout(2000)

        # 6. 페이지에 있는 모든 무료 아이템 버튼 찾기
        free_buttons = page.locator('[data-testid="free-button"]')
        total = free_buttons.count()

        skus = []
        for i in range(total):
            sku = free_buttons.nth(i).get_attribute("data-sku")
            if sku:
                skus.append(sku)

        if not skus:
            has_error = True
            logs.append("무료 아이템을 찾지 못했습니다.")

        # 7. 찾은 무료 아이템을 하나씩 순서대로 수령
        for sku in skus:
            btn = page.locator(f'[data-testid="free-button"][data-sku="{sku}"]').first
            btn.scroll_into_view_if_needed()

            if btn.is_visible() and btn.is_enabled():
                btn.click()
                claimed_modal = page.locator('[data-testid="claimed-item-modal"]')
                try:
                    claimed_modal.wait_for(state="visible", timeout=10000)
                    claimed_count += 1
                    logs.append(f"✅ `{sku}` 수령 완료!")
                    back_btn = claimed_modal.get_by_role("button", name="Back to store")
                    if back_btn.is_visible():
                        back_btn.click()
                        claimed_modal.wait_for(state="hidden", timeout=10000)
                    page.wait_for_timeout(1000)
                except Exception:
                    has_error = True
                    logs.append(f"⚠️ `{sku}` 클릭 후 완료 팝업 확인 필요")
            else:
                already_count += 1
                logs.append(f"⏭️ `{sku}` 이미 수령됨 ({btn.inner_text()})")

    except Exception as e:
        has_error = True
        logs.append(f"❌ 오류 발생: {e}")

    finally:
        page.screenshot(path=screenshot_path, full_page=False)
        context.close()
        summary = f"**[{label}]**\n" + "\n".join(logs)
        print(summary)
        send_discord(summary, screenshot_path)

    if has_error:
        return "failed"
    if claimed_count > 0:
        return "claimed"
    if already_count > 0:
        return "already"
    return "failed"

def run():
    players = load_players()
    if not players:
        raise ValueError("players.txt와 PLAYER_ID Secret이 모두 비어 있습니다!")

    print(f"총 {len(players)}개의 계정을 처리합니다.")
    claimed_list = []
    already_list = []
    failed_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for idx, (pid, memo) in enumerate(players, start=1):
            display_name = memo if memo else f"{idx}번 계정"
            status = claim_for_player(browser, idx, pid, memo)
            if status == "claimed":
                claimed_list.append(display_name)
            elif status == "already":
                already_list.append(display_name)
            else:
                failed_list.append(display_name)
        browser.close()

    claimed_text = ", ".join(claimed_list) if claimed_list else "없음"
    already_text = ", ".join(already_list) if already_list else "없음"
    failed_text = ", ".join(failed_list) if failed_list else "없음"

    final_msg = (
        f"🎉 **모든 계정의 무료 아이템 수령이 끝났습니다!** (총 {len(players)}개 계정)\n"
        f"✅ **받은 계정 ({len(claimed_list)}):** {claimed_text}\n"
        f"⏭️ **이미 수령됨 ({len(already_list)}):** {already_text}\n"
        f"❌ **못 받은 계정 ({len(failed_list)}):** {failed_text}"
    )
    print(final_msg)
    send_discord(final_msg)

if __name__ == "__main__":
    run()
