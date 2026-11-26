import os
from playwright.sync_api import sync_playwright

STORE_URL = "https://store.eternalhero.rivvy.games/"

def load_player_ids():
    ids = []
    # 1. players.txt 파일이 있으면 한 줄씩 읽어옵니다.
    if os.path.exists("players.txt"):
        with open("players.txt", "r", encoding="utf-8") as f:
            for line in f:
                # '#' 뒤의 메모를 제거하고 앞뒤 공백을 정리합니다.
                pid = line.split("#", 1)[0].strip()
                if pid:
                    ids.append(pid)

    # 2. players.txt가 비어 있으면 기존 Secrets(PLAYER_ID)에서 가져옵니다.
    if not ids:
        raw_ids = os.environ.get("PLAYER_ID", "")
        ids = [x.strip() for x in raw_ids.replace(",", "\n").splitlines() if x.strip()]

    return ids

def claim_for_player(browser, idx, player_id):
    print(f"\n--- [{idx}번 계정] 수령 시작 ---")
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

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
        print(f"[{idx}번 계정] 로그인 성공!")
        page.wait_for_timeout(2000)

        # 6. 페이지에 있는 '모든' 무료 아이템 버튼 찾기
        free_buttons = page.locator('[data-testid="free-button"]')
        total = free_buttons.count()
        print(f"[{idx}번 계정] 발견된 무료 아이템 개수: {total}개")

        skus = []
        for i in range(total):
            sku = free_buttons.nth(i).get_attribute("data-sku")
            if sku:
                skus.append(sku)

        # 7. 찾은 무료 아이템을 하나씩 순서대로 수령
        for sku in skus:
            btn = page.locator(f'[data-testid="free-button"][data-sku="{sku}"]').first
            btn.scroll_into_view_if_needed()

            if btn.is_visible() and btn.is_enabled():
                print(f"[{idx}번 계정] '{sku}' 수령 시도...")
                btn.click()

                claimed_modal = page.locator('[data-testid="claimed-item-modal"]')
                try:
                    claimed_modal.wait_for(state="visible", timeout=10000)
                    print(f"[{idx}번 계정] '{sku}' 수령 완료!")
                    back_btn = claimed_modal.get_by_role("button", name="Back to store")
                    if back_btn.is_visible():
                        back_btn.click()
                        claimed_modal.wait_for(state="hidden", timeout=10000)
                    page.wait_for_timeout(1000)
                except Exception as modal_err:
                    print(f"[{idx}번 계정] '{sku}' 완료 팝업 대기 중 참고사항: {modal_err}")
            else:
                print(f"[{idx}번 계정] '{sku}' 이미 수령됨 (상태: {btn.inner_text()})")

    except Exception as e:
        print(f"[{idx}번 계정] 오류 발생: {e}")

    finally:
        page.screenshot(path=f"result_{idx}.png", full_page=False)
        context.close()

def run():
    player_ids = load_player_ids()
    if not player_ids:
        raise ValueError("players.txt와 PLAYER_ID Secret이 모두 비어 있습니다!")

    print(f"총 {len(player_ids)}개의 계정을 처리합니다.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for idx, pid in enumerate(player_ids, start=1):
            claim_for_player(browser, idx, pid)
        browser.close()

if __name__ == "__main__":
    run()
