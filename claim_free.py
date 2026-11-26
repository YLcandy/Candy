import os
from playwright.sync_api import sync_playwright

PLAYER_ID = os.environ.get("PLAYER_ID", "").strip()
STORE_URL = "https://store.eternalhero.rivvy.games/"

def run():
    if not PLAYER_ID:
        raise ValueError("PLAYER_ID가 비어 있습니다! Repository secrets에 PLAYER_ID를 등록해 주세요.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

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
            inp.press_sequentially(PLAYER_ID, delay=50)
            page.wait_for_timeout(500)

            # 4. 입력창과 한 세트인 'Log in' 버튼 클릭
            login_box = inp.locator("xpath=ancestor::*[.//button[contains(., 'Log in')]][1]")
            login_box.get_by_role("button", name="Log in").click()

            # 5. 로그인 완료 대기
            inp.wait_for(state="hidden", timeout=15000)
            print("로그인 성공!")
            page.wait_for_timeout(2000)

            # 6. 무료 아이템(echo_shard_pack_free) 상태 확인 및 수령
            free_btn = page.locator('[data-sku="echo_shard_pack_free"]').first
            free_btn.scroll_into_view_if_needed()

            if free_btn.is_enabled():
                free_btn.click()
                # 수령 완료 팝업이 뜰 때까지 대기
                claimed_modal = page.locator('[data-testid="claimed-item-modal"]')
                claimed_modal.wait_for(state="visible", timeout=15000)
                print("무료 아이템 수령 완료!")
                page.wait_for_timeout(1000)
            else:
                print("이미 오늘 무료 아이템을 수령했습니다. (상태:", free_btn.inner_text(), ")")

        finally:
            page.screenshot(path="result.png", full_page=False)
            browser.close()

if __name__ == "__main__":
    run()
