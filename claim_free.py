import os
from playwright.sync_api import sync_playwright

# GitHub Secrets에 저장한 PLAYER_ID를 불러옵니다.
PLAYER_ID = os.environ["PLAYER_ID"]
STORE_URL = "https://store.eternalhero.rivvy.games/"

def run():
    with sync_playwright() as p:
        # 1. 크롬 브라우저를 화면 없이(headless) 실행합니다.
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 2. 웹 상점 사이트로 이동합니다.
        page.goto(STORE_URL, wait_until="networkidle")

        # 3. 쿠키 안내 팝업이 뜨면 닫기(Dismiss) 버튼을 누릅니다.
        dismiss_btn = page.get_by_role("button", name="Dismiss")
        if dismiss_btn.is_visible():
            dismiss_btn.click()

        # 4. 로그인 버튼을 누르고 Player ID를 입력합니다.
        page.get_by_role("button", name="Log in").first.click()
        page.locator("input").first.fill(PLAYER_ID)
        page.get_by_role("button", name="Log in").last.click()
        page.wait_for_timeout(3000)  # 로그인 처리까지 3초 대기

        # 5. 'Daily Free Echo Shards (100)' 카드 근처의 'Get free' 버튼을 누릅니다.
        free_btn = page.get_by_role("button", name="Get free").first
        free_btn.scroll_into_view_if_needed()
        free_btn.click()
        page.wait_for_timeout(2000)

        # 6. 장바구니(Cart)로 이동해 최종 수령/결제 버튼이 있으면 누릅니다.
        cart_btn = page.get_by_role("button", name="Cart")
        if cart_btn.is_visible():
            cart_btn.click()
            page.wait_for_timeout(2000)

        # 7. 잘 실행되었는지 눈으로 확인할 수 있도록 스크린샷을 남깁니다.
        page.screenshot(path="result.png", full_page=True)
        browser.close()

if __name__ == "__main__":
    run()
