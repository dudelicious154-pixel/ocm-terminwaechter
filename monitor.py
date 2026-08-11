import os
import requests
from playwright.sync_api import sync_playwright

URL = "https://app.arzt-direkt.de/ocm-otk/booking?katid=68d12673a45e3ed89827cbd5"


def send_notification(message):
    topic = os.environ.get("NTFY_TOPIC")

    if not topic:
        raise RuntimeError("NTFY_TOPIC ist in GitHub nicht vorhanden!")

    print("NTFY_TOPIC wurde von GitHub geladen.")
    print("Sende Nachricht an ntfy...")

    response = requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": "OCM Termin gefunden!",
            "Priority": "urgent",
            "Tags": "rotating_light"
        },
        timeout=20
    )

    print("NTFY HTTP-Status:", response.status_code)
    print("NTFY Antwort:", response.text)

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

            send_notification(
                "OCM München: Es könnte ein Termin bei Team Prof. Dr. Dienst / "
                "Hr. Dakkak für gesetzlich Versicherte ohne Selektivvertrag "
                "frei sein.\n\n"
                "Jetzt sofort Terminportal prüfen:\n"
                + URL
            )

            print("Push-Nachricht wurde gesendet.")

        browser.close()


if __name__ == "__main__":
    # Nur zum Testen der Push-Verbindung.
    # Wenn alles funktioniert, entfernen wir diese Zeile wieder.
    send_notification("TEST: Dein OCM-Terminwächter funktioniert!")

    check_ocm()
