import os
from playwright.sync_api import sync_playwright

PLAYER_ID = os.environ.get("PLAYER_ID", "").strip()
STORE_URL = "https://store.eternalhero.rivvy.games/"

def run():
    if not PLAYER_ID:
        raise ValueError("PLAYER_ID가 비어 있습니다! Repository secrets에 PLAYER_ID를 등록해 주세요.")
    print("Secret에서 불러온 ID 글자 수:", len(PLAYER_ID))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        modal = page.locator(".user-id-modal")

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
            print("입력창에 들어간 글자 수:", len(inp.input_value()))
            page.wait_for_timeout(500)

            # 4. 입력창과 한 세트인 'Log in' 버튼 클릭
            login_box = inp.locator("xpath=ancestor::*[.//button[contains(., 'Log in')]][1]")
            login_box.get_by_role("button", name="Log in").click()
            page.wait_for_timeout(4000)

            print("로그인 박스 내용:", login_box.inner_text().replace("\n", " | "))

            # 5. 무료 아이템 클릭
            free_btn = page.locator('[data-sku="echo_shard_pack_free"]').first
            free_btn.scroll_into_view_if_needed()
            free_btn.click()
            page.wait_for_timeout(3000)

            # 6. 장바구니 클릭
            cart_btn = page.locator("button:has-text('Cart'):visible").first
            if cart_btn.is_visible():
                cart_btn.click()
                page.wait_for_timeout(2000)

        finally:
            if modal.is_visible():
                print("팝업 내용:", modal.inner_text().replace("\n", " | "))
            page.screenshot(path="result.png", full_page=False)
            browser.close()

if __name__ == "__main__":
    run()
