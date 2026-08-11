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

        page = browser.new_page(
            viewport={"width": 1400, "height": 1000}
        )

        print("OCM-Seite wird geöffnet...")

        page.goto(
            URL,
            wait_until="networkidle",
            timeout=60000
        )

        # Waren Sie schon einmal bei uns? -> Nein
        print("Klicke auf Nein...")
        page.get_by_text("Nein", exact=True).click()

        # Versicherung -> Gesetzlich
        print("Klicke auf Gesetzlich...")
        page.get_by_text("Gesetzlich", exact=True).click()

        # Start-Button
        print("Klicke auf Start...")
        page.get_by_role("button", name="Start").click()

        # Warten, bis die nächste Seite geladen ist
        page.wait_for_timeout(5000)

        print("Terminseite geladen.")

        # Gesamten sichtbaren Text auslesen
        text = page.locator("body").inner_text()

        print("----- SEITENTEXT -----")
        print(text)
        print("----------------------")

        target = "Gesetzlich Versichert ohne Selektivvertrag"

        # Prüfen, ob die gewünschte Terminart überhaupt vorhanden ist
        if target not in text:
            print("FEHLER: Die gewünschte Terminart wurde nicht gefunden.")
            browser.close()
            raise RuntimeError(
                "Die Terminart 'Gesetzlich Versichert ohne Selektivvertrag' "
                "wurde auf der Seite nicht gefunden."
            )

        # Nur den Bereich direkt nach der gewünschten Terminart prüfen
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

        browser.close()


if __name__ == "__main__":
    check_ocm()
