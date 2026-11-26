import os
from playwright.sync_api import sync_playwright

PLAYER_ID = os.environ["PLAYER_ID"]
STORE_URL = "https://store.eternalhero.rivvy.games/"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. 웹 상점 사이트로 이동
            page.goto(STORE_URL, wait_until="networkidle")

            # 2. 쿠키 안내 팝업이 뜨면 닫기
            dismiss_btn = page.get_by_role("button", name="Dismiss")
            if dismiss_btn.is_visible():
                dismiss_btn.click()

            # 3. 상단 'Log in' 버튼을 눌러 로그인 팝업 열기
            page.get_by_role("button", name="Log in").first.click()

            # 4. 로그인 팝업(.user-id-modal) 안의 입력창에 Player ID 입력 후 로그인
            modal = page.locator(".user-id-modal")
            modal.wait_for(state="visible", timeout=10000)
            modal.locator("input").first.fill(PLAYER_ID)
            modal.get_by_role("button", name="Log in").click()

            # 5. 로그인 팝업이 닫힐 때까지 대기
            modal.wait_for(state="hidden", timeout=15000)
            page.wait_for_timeout(2000)

            # 6. 무료 아이템(echo_shard_pack_free) 버튼 클릭
            free_btn = page.locator('[data-sku="echo_shard_pack_free"]').first
            free_btn.scroll_into_view_if_needed()
            free_btn.click()
            page.wait_for_timeout(3000)

            # 7. 장바구니(Cart) 버튼이 있으면 열어보기
            cart_btn = page.get_by_role("button", name="Cart")
            if cart_btn.is_visible():
                cart_btn.click()
                page.wait_for_timeout(2000)

        finally:
            # 오류가 나든 성공하든 마지막 화면을 무조건 스크린샷으로 저장
            page.screenshot(path="result.png", full_page=True)
            browser.close()

if __name__ == "__main__":
    run()
