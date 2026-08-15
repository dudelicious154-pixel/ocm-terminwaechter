import os
import requests
from playwright.sync_api import sync_playwright

URL = "https://app.arzt-direkt.de/ocm-otk/booking?katid=68d12673a45e3ed89827cbd5"


def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN fehlt in GitHub!")

    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID fehlt in GitHub!")

    print("Telegram-Daten wurden von GitHub geladen.")
    print("Sende Telegram-Nachricht...")

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=20
    )

    print("Telegram HTTP-Status:", response.status_code)
    print("Telegram Antwort:", response.text)

    response.raise_for_status()


def check_ocm():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={"width": 1400, "height": 1000}
        )

        print("OCM-Seite wird geöffnet...")

        page.goto(
            URL,
            wait_until="networkidle",
            timeout=60000
        )

        page.get_by_text(
            "Waren Sie schon einmal bei uns?"
        ).wait_for(timeout=30000)

        print("Klicke auf Nein...")
        page.get_by_text("Nein", exact=True).click()

        page.wait_for_timeout(1000)

        print("Klicke auf Gesetzlich...")
        page.get_by_text("Gesetzlich", exact=True).click()

        print("Warte auf Terminseite...")

        target = "Gesetzlich Versichert ohne Selektivvertrag"

        page.get_by_text(
            target,
            exact=False
        ).wait_for(timeout=30000)

        print("Terminseite wurde geladen.")

        text = page.locator("body").inner_text()

        print("----- SEITENTEXT -----")
        print(text)
        print("----------------------")

        if target not in text:
            browser.close()
            raise RuntimeError(
                "Die gewünschte Terminart wurde nicht gefunden."
            )

        position = text.find(target)
        relevant_text = text[position:position + 500]

        print("----- RELEVANTER BEREICH -----")
        print(relevant_text)
        print("------------------------------")

        if "Keine freien Termine" in relevant_text:
            print("Noch keine freien Termine.")

        else:
            print("ACHTUNG: Möglicher freier Termin gefunden!")

            send_telegram(
                "🚨 OCM-TERMIN MÖGLICHERWEISE FREI!\n\n"
                "Team Prof. Dr. Dienst / Hr. Dakkak\n"
                "Gesetzlich versichert ohne Selektivvertrag\n\n"
                "Jetzt sofort prüfen:\n"
                + URL
            )

            print("Telegram-Nachricht wurde gesendet.")

        browser.close()


if __name__ == "__main__":
    check_ocm()
