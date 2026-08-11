import os
import requests
from playwright.sync_api import sync_playwright

URL = "https://app.arzt-direkt.de/ocm-otk/booking?katid=68d12673a45e3ed89827cbd5"

def send_notification(message):
    topic = os.environ["NTFY_TOPIC"]

    requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": "OCM Termin gefunden!",
            "Priority": "urgent",
            "Tags": "rotating_light"
        },
        timeout=20
    )

def check_ocm():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)

        # "Waren Sie schon einmal bei uns?" -> Nein
        page.get_by_text("Nein", exact=True).click()

        # Versicherung -> Gesetzlich
        page.get_by_text("Gesetzlich", exact=True).click()

        # Start
        page.get_by_text("Start", exact=True).click()

        page.wait_for_timeout(5000)

        # Text der geladenen Terminseite auslesen
        text = page.locator("body").inner_text()

        print(text)

        target = "Gesetzlich Versichert ohne Selektivvertrag"

        if target not in text:
            print("Gesuchte Terminart wurde nicht gefunden.")
            browser.close()
            return

        # Wir schauen uns den Bereich nach unserer Terminart an.
        position = text.find(target)
        relevant_text = text[position:position + 500]

        print("Relevanter Bereich:")
        print(relevant_text)

        if "Keine freien Termine" not in relevant_text:
            print("MÖGLICHER TERMIN GEFUNDEN!")
            send_notification(
                "Bei OCM München könnte ein Termin bei Team Prof. Dr. Dienst / "
                "Hr. Dakkak für gesetzlich Versicherte ohne Selektivvertrag "
                "frei sein. Jetzt Terminportal prüfen:\n" + URL
            )
        else:
            print("Noch keine freien Termine.")

        browser.close()


if __name__ == "__main__":
    check_ocm()
