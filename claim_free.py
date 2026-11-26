import os
from playwright.sync_api import sync_playwright

PLAYER_ID = os.environ["PLAYER_ID"]
STORE_URL = "https://store.eternalhero.rivvy.games/"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        try:
            # 1. 웹 상점 사이트로 이동
            page.goto(STORE_URL, wait_until="networkidle")

            # 2. 쿠키 안내 팝업이 뜨면 닫기
            dismiss_btn = page.get_by_role("button", name="Dismiss")
            if dismiss_btn.is_visible():
                dismiss_btn.click()

            # 3. 화면에 실제로 보이는 'Log in' 버튼 클릭
            modal = page.locator(".user-id-modal")
            if not modal.is_visible():
                page.locator("button:has-text('Log in'):visible").first.click()
                page.wait_for_timeout(1000)

            # 4. 첫 번째 버튼으로 팝업이 안 열렸다면 마지막 'Log in' 버튼 클릭
            if not modal.is_visible():
                page.locator("button:has-text('Log in'):visible").last.click()

            # 5. 로그인 팝업(.user-id-modal) 안의 입력창에 Player ID 입력 후 로그인
            modal.wait_for(state="visible", timeout=10000)
            modal.locator("input:visible").first.fill(PLAYER_ID)
            modal.locator("button:has-text('Log in'):visible").first.click()

            # 6. 로그인 팝업이 닫힐 때까지 대기
            modal.wait_for(state="hidden", timeout=15000)
            page.wait_for_timeout(2000)

            # 7. 무료 아이템(echo_shard_pack_free) 버튼 클릭
            free_btn = page.locator('[data-sku="echo_shard_pack_free"]').first
            free_btn.scroll_into_view_if_needed()
            free_btn.click()
            page.wait_for_timeout(3000)

            # 8. 장바구니(Cart) 버튼이 있으면 열어보기
            cart_btn = page.locator("button:has-text('Cart'):visible").first
            if cart_btn.is_visible():
                cart_btn.click()
                page.wait_for_timeout(2000)

        finally:
            # 오류가 나든 성공하든 마지막 화면을 무조건 스크린샷으로 저장
            page.screenshot(path="result.png", full_page=True)
            browser.close()

if __name__ == "__main__":
    run()
