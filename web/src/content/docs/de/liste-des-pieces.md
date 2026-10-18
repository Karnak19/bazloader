---
title: Stückliste
description: Alles, was du für einen BULLOADER+ bestellen musst, mit den Fallen, die du bei der Auswahl vermeiden solltest.
---

Diese Seite ist eine Einkaufsliste. Alles gibt es bei Online-Elektronikhändlern (AliExpress und
Co.). Links und Preise stehen hier nicht, die ändern sich zu schnell. Stattdessen gibt es
**Suchbegriffe** zum Kopieren und vor allem **das, was du auf der Produktseite prüfen solltest**,
bevor du auf „Kaufen“ klickst. Die Suchbegriffe sind absichtlich auf Englisch: So findet man auf
diesen Seiten am meisten.

Die Werte (Widerstände, Kondensatoren, Pins) stammen von der Seite
[Verkabelung](/bulloader-plus/de/cablage/). Sollten die beiden Seiten einmal voneinander abweichen,
gilt die Verkabelung und, noch darüber,
[`firmware/src/config.h`](https://github.com/Karnak19/bulloader-plus/blob/main/firmware/src/config.h).

Die vorgeschlagenen Mengen enthalten etwas Reserve: Diese Teile kosten ein paar Cent bis ein paar
Euro, und drei Wochen auf eine zweite Lieferung für eine beschädigte LED zu warten, kostet viel
mehr.

## Vor der Bestellung: die Spannung des Servos

:::danger[Prüfe dein Servo, bevor du bestellst]
Das Original-Servo des BULLOADER hängt **direkt am 2S-Akku**, der voll geladen **8,4 V** erreicht.
Viele „35-kg“-Servos sind nur für **4,8 bis 6,8 V** ausgelegt: Darüber werden sie heiß und brennen
irgendwann durch. Nur sogenannte **HV**-Servos (*High Voltage*) vertragen 8,4 V.

1. Lies die Typenbezeichnung auf dem Etikett des Servos ab und such sein Datenblatt.
2. **Reicht der Spannungsbereich bis 8,4 V (HV-Servo)**: Es muss nichts dazu, das Servo bleibt am
   Akku.
3. **Wenn nicht**, bestell zusätzlich ein **BEC** (einen kleinen Spannungsregler aus dem
   Modellbau) oder einen zweiten Wandler, nur für das Servo. Worauf es ankommt:
   - **der Strom**: mindestens der **Blockierstrom** des Servos (*Stall Current*, den es zieht,
     wenn es blockiert wird und dagegen ankämpft; steht im Datenblatt). Bei einem 35-kg-Servo sind
     das mehrere Ampere: Ziel sind **5 A Dauerstrom oder mehr**;
   - **die Ausgangsspannung**: im Bereich des Servos, zum Beispiel **6,0 V** für ein Servo mit
     4,8–6,8 V. UBECs aus dem Modellbau haben oft einen Jumper für 5 V / 6 V;
   - **der Eingang**: 2S-tauglich (7,4 V, voll 8,4 V).

   Suchbegriffe: „UBEC 5A 6V“, „UBEC 2-6S 5A“.

**Ein MP1584 reicht für das Servo nicht.** Der aus dieser Liste versorgt nur den ESP32: Er schafft
etwa 3 A Spitze, weit weniger, als ein großes blockiertes Servo zieht.
:::

Wenn du ein BEC einbaust, kommt der 470-µF-Kondensator an dessen Ausgang, so nah wie möglich am
Servo.

## Was du schon hast

Diese Teile stammen aus dem Original-BULLOADER und werden wiederverwendet. **Nicht bestellen.**

| Teil                           | Menge    | Status       | Wofür                                                                                           |
| ------------------------------ | -------- | ------------ | ----------------------------------------------------------------------------------------------- |
| 2S-LiPo-Akku (7,4 V)           | 1        | schon da     | Versorgt alles. Das passende LiPo-Ladegerät ebenso.                                             |
| Servo 35 kg 360° (Endlosdrehung) | 1      | schon da     | Treibt die Mechanik an. Zu seiner Spannung siehe den Kasten oben.                               |
| Ein/Aus-Schalter               | 1        | schon da     | Hauptschalter zwischen dem Akku und allem anderen.                                              |
| Taster (der alte 12-V-Taster)  | 1        | schon da     | Wird zum **GO**-Taster: ein einfacher Kontakt zwischen GPIO 4 und Masse, von den alten 12 V getrennt. |

## Hauptelektronik

| Teil | Bestellmenge | Genaue Spezifikation | Worauf es bei der Auswahl ankommt | Wofür |
| ---- | ------------ | -------------------- | --------------------------------- | ----- |
| ESP32-C3 SuperMini | **3** (1 im Einsatz + 2 Reserve) | Board ESP32-**C3** „SuperMini“, USB-C, etwa 22 × 18 mm. Suche: „ESP32-C3 SuperMini“. | Wirklich **C3**: Es gibt „SuperMini“-Boards mit S3, C6 oder H2, auf denen diese Firmware nicht läuft und die Pinbelegung nicht passt. Manche Chargen haben eine schwache Antenne (schlechte Bluetooth-Reichweite): Wer mehrere kauft, kann das beste behalten. Sie kosten wenig. Die Stiftleisten liegen meist lose bei, nicht eingelötet. | Das Gehirn: zählt die BBs, steuert das Servo, das Display und Bluetooth. |
| Step-down-Wandler MP1584 | **2** (1 + 1 Reserve) | Modul MP1584**EN**, etwa 22 × 17 mm, Eingang bis ~28 V, ~3 A Spitze. Am besten mit **fester 5-V-Ausgangsspannung**, sonst die **einstellbare** Version (kleine Trimmpoti-Schraube). Suche: „MP1584EN 5V fixed output“ oder „MP1584EN step down adjustable“. | Die Version mit **festen 5 V** ist die sicherste: Es gibt nichts einzustellen, also auch kein Trimmpoti, das man falsch drehen kann. Eine einstellbare geht auch, liefert ab Werk aber irgendeine Spannung, manchmal nahe an der des Akkus: Sie **muss** mit dem Multimeter auf 5,0 V eingestellt werden. In beiden Fällen **den Ausgang mit dem Multimeter messen, bevor der ESP32 angeschlossen wird**. Kein anderes Modul stattdessen: Der „Mini-360“ zum Beispiel hat einen anderen Chip. | Erzeugt aus dem Akku die 5 V für den ESP32. Nicht für das Servo. |

## Infrarotsensor

| Teil | Bestellmenge | Genaue Spezifikation | Worauf es bei der Auswahl ankommt | Wofür |
| ---- | ------------ | -------------------- | --------------------------------- | ----- |
| Infrarot-LED 3 mm | **1 Beutel** (10 bis 50 Stück, 1 wird gebraucht) | IR-Sende-LED, **3-mm**-Gehäuse, **940 nm**. Suche: „3mm IR LED 940nm emitter“. | Die **Wellenlänge**: **940 nm**, dieselbe wie beim Fototransistor. Das ist der häufigste Fehler: Eine 850-nm-LED (sie glimmt dunkelrot) mit einem 940-nm-Sensor, oder umgekehrt, ergibt ein schwaches, unzuverlässiges Signal. 3-mm-Gehäuse, nicht 5 mm: Der Ring ist für 3 mm konstruiert. | Sendet den Strahl, den die BBs unterbrechen. |
| Fototransistor 3 mm | **1 Beutel** (10 bis 50 Stück, 1 wird gebraucht) | NPN-Fototransistor, **3-mm**-Gehäuse, **940 nm**, 2 Beine. Am besten mit **dunklem Epoxid** (schwarz oder sehr dunkles Violett). Suche: „3mm phototransistor 940nm black“. | **940 nm**, wie die LED. **Dunkles** Epoxid filtert sichtbares Licht heraus: weniger Ärger in praller Sonne, also vorzuziehen. Vorsicht vor Verwechslungen: Ein „IR-Empfänger“ mit **3 Beinen** (VS1838B, TSOP…) ist ein Fernbedienungsempfänger und funktioniert hier nicht. Eine Fotodiode sieht genauso aus, liefert aber ein viel schwächeres Signal: Auf der Produktseite muss *phototransistor* stehen. | Sieht den Strahl und damit jede BB, die durchkommt. |

## Bedienung

| Teil | Bestellmenge | Genaue Spezifikation | Worauf es bei der Auswahl ankommt | Wofür |
| ---- | ------------ | -------------------- | --------------------------------- | ----- |
| Drehgeber KY-040 | **2** (1 + 1 Reserve) | Modul **KY-040**: Drehgeber mit Rastung und Drucktaster, auf seiner kleinen Platine mit den Pull-up-Widerständen, 5 Pins (CLK, DT, SW, +, GND). Suche: „KY-040 rotary encoder module“. | Das **Modul auf Platine** nehmen, nicht den nackten Drehgeber. Er läuft an **3,3 V** (nicht 5 V), siehe [Verkabelung](/bulloader-plus/de/cablage/). Springt eine Raste um 2 statt um 1 weiter (oder umgekehrt), lässt sich das in `config.h` einstellen, das Modul muss nicht zurück. | Die Anzahl der BBs einstellen, mit einem Klick bestätigen. |
| Knopf für den Drehgeber | **2** | Drehknopf für eine **6-mm**-Achse, groß (25 mm Durchmesser oder mehr), gerändelt oder gummiert. Suche: „knob 6mm shaft knurled“. | Schau dir die Achse deines KY-040 an: **geriffelt** (Rillen rundherum) oder **D-förmig** (eine abgeflachte Seite). Der Knopf muss dazu passen. Groß und gerändelt, damit er sich **mit Handschuhen** bedienen lässt. Manche KY-040 kommen mit einem kleinen Knopf, meist zu klein. | Auf dem Spielfeld am Knopf drehen. |
| OLED-Display 0,96" | **2** (1 + 1 Reserve) | OLED **0,96"**, **128 × 64**, Controller **SSD1306**, **4-Pin-I2C**-Schnittstelle (VCC, GND, SCL, SDA). Suche: „0.96 OLED SSD1306 I2C 4 pin 128x64“. | **4 Pins, I2C.** Die **7-Pin**-Versionen (SPI) sind die falschen. **Die Reihenfolge von VCC / GND ist je nach Händler verschieden** (GND-VCC-SCL-SDA oder VCC-GND-SCL-SDA): Vor dem Löten die Beschriftung lesen, vertauscht ist das Display hinüber. I2C-Adresse meist **0x3C**, manchmal **0x3D**. Lieber einfarbig (weiß oder blau): Die „gelb/blauen“ haben oben einen fest gelben Streifen. | Zeigt den Zustand, den Zählerstand und den Akku an. |

## Passive Bauteile

| Teil | Bestellmenge | Genaue Spezifikation | Worauf es bei der Auswahl ankommt | Wofür |
| ---- | ------------ | -------------------- | --------------------------------- | ----- |
| Kondensator 470 µF | **5** (1 wird gebraucht) | Elektrolytkondensator **470 µF**, **16 V oder mehr**. Suche: „470uF 16V electrolytic capacitor“. | Die Spannung: **mindestens 16 V** (25 V geht auch, er ist nur etwas größer). Einer mit 10 V oder 6,3 V hält die 8,4 V des Akkus nicht aus. Er ist **gepolt**: Das `−`-Bein ist mit einem Streifen auf dem Gehäuse markiert. | An der Versorgung des Servos, so nah wie möglich daran: verhindert Spannungseinbrüche, wenn das Servo anläuft. |
| Kondensator 100 nF | **10** (1 wird gebraucht) | Keramikkondensator **100 nF** (Aufdruck „104“), 50 V. Suche: „100nF 104 ceramic capacitor“. | Nichts Kniffliges. Wird oft zu 50 oder 100 Stück verkauft, das ist normal. | Zwischen GPIO 0 und Masse: glättet die Akkumessung. |
| Widerstand 220 Ω | im Sortiment (1 wird gebraucht) | 220 Ω, 1/4 W. | | In Reihe mit der IR-LED (etwa 10 mA). |
| Widerstand 10 kΩ | im Sortiment (1 wird gebraucht) | 10 kΩ, 1/4 W. | | Pull-up vom Fototransistor nach 3,3 V. |
| Widerstand 100 kΩ | im Sortiment (1 wird gebraucht) | 100 kΩ, 1/4 W. | | Akku-Spannungsteiler, Akkuseite. |
| Widerstand 20 kΩ | im Sortiment (1 wird gebraucht) | 20 kΩ, 1/4 W. | Genau **20 kΩ**: Die Firmware rechnet die Akkuspannung mit 100 kΩ / 20 kΩ aus. Bei 8,4 V sieht der Pin des ESP32 dann 1,40 V. | Akku-Spannungsteiler, Masseseite. |
| Widerstandssortiment | **1** | Sortiment Metallschichtwiderstände 1/4 W, 1 %, mit **220 Ω, 10 kΩ, 20 kΩ und 100 kΩ**. Suche: „metal film resistor kit 1/4W 1%“. | Am einfachsten: Ein Sortiment deckt alle vier Werte ab und ist auch später nützlich. In der Werteliste des Sortiments nachsehen, ob **20 kΩ** dabei ist (übliche Sortimente mit 30 Werten haben ihn). Ein **1 MΩ** aus dem Sortiment ist außerdem praktisch, falls sich der IR-Empfänger als Fotodiode statt als Fototransistor herausstellt. | Alle Widerstände oben. |

## Verkabelung und Kleinteile

| Teil | Bestellmenge | Genaue Spezifikation | Worauf es bei der Auswahl ankommt | Wofür |
| ---- | ------------ | -------------------- | --------------------------------- | ----- |
| Lochrasterplatine | **1 Pack** (5 bis 10 Platinen) | Lochrasterplatine mit Lötpunkten, Raster **2,54 mm**, doppelseitig, 5 × 7 cm (zum Zuschneiden). Suche: „PCB prototype board double sided 5x7“. | Lötpunkte (einer pro Loch), keine Streifen. Doppelseitig, da halten die Lötpunkte besser. Die genauen Maße des Elektronikhalters kommen später: Eine 5 × 7-cm-Platine lässt sich leicht zuschneiden. | Trägt den ESP32, den Wandler und die kleinen Bauteile. |
| Buchsenleiste 2,54 mm | **1 Pack** | Trennbare Buchsenleisten, Raster 2,54 mm. Suche: „female pin header 2.54mm“. | Damit lässt sich der ESP32 einstecken statt einlöten: In zwei Sekunden ausgetauscht. | Sockel für den ESP32 auf der Platine. |
| Dicke Silikonlitze | **1 m** rot + **1 m** schwarz | Weiche Silikonlitze **18 AWG** (etwa 0,8 mm²). Suche: „silicone wire 18AWG“. | Silikon: flexibel und schmilzt nicht unter dem Lötkolben. Dick genug für den **Strom des Servos**, der in Ampere gemessen wird. | Akku, Schalter, Servo (oder BEC), Eingang des Wandlers. |
| Dünne Litze für Signale | **1 Pack** (mehrere Farben) | Silikonlitze **26 oder 28 AWG**, mehrere Farben. Suche: „silicone wire 26AWG 10 colors“. | Mehrere Farben, damit nichts verwechselt wird (eine Farbe pro Funktion). Silikon lässt sich in einem engen Gehäuse gut biegen. | IR-LED, Fototransistor, Drehgeber, Display, GO-Taster, Servosignal. |
| JST-XH-Steckverbinder 2,54 mm | **1 Set** (2, 3, 4 und 5 Pins) | JST-XH-Set 2,54 mm: Einlötbuchsen und Stecker. Am einfachsten: **fertig gecrimpte Kabel**. Suche: „JST XH 2.54 pre-crimped cable“ oder „JST XH connector kit“. | Damit lässt sich jedes Teil (Display, Drehgeber, IR-Sensor, Taster) **abstecken** und ohne Entlöten ausbauen. Zum Crimpen von Steckern braucht man eine Crimpzange: Fertig gecrimpte Kabel ersparen das. Dupont-Stecker gehen auch, halten bei Vibrationen aber schlechter. **Nicht für den Strom des Servos**: Dafür seinen Originalstecker behalten. | Die Elektronik mit der Platine verbinden. |
| Schraube M3 × 10 | **1 Pack** (1 wird gebraucht) | Zylinderschraube mit Innensechskant **M3 × 10 mm**. Suche: „M3 x 10 socket head screw“. | **10 mm** lang. Ein M3-Sortiment von 6 bis 20 mm ist auch für später nützlich (Elektronikhalter). | Schließt den IR-Ring um das Rohr. |
| Mutter M3 | **1 Pack** (1 wird gebraucht) | Standard-Sechskantmutter **M3** (5,5 mm Schlüsselweite, 2,4 mm dick). Suche: „M3 hex nut“. | Eine normale Sechskantmutter, keine Bundmutter und keine Sicherungsmutter mit Nylonring: Sie muss in die sechseckige Aussparung des Rings passen. | Sitzt im IR-Ring, gegenüber der Schraube. |
| Schwarzer Schrumpfschlauch | **1 Sortiment** | **Schwarzer** Schrumpfschlauch, Durchmesser 1,5 bis 6 mm. Suche: „heat shrink tube black assortment“. | **Schwarz**: Er isoliert nicht nur die Lötstellen, sondern schützt auch die Rückseite des Fototransistors vor Licht. | Lötstellen isolieren, und den Fototransistor samt Beinen abschatten. |

## Druck

| Teil | Bestellmenge | Genaue Spezifikation | Worauf es bei der Auswahl ankommt | Wofür |
| ---- | ------------ | -------------------- | --------------------------------- | ----- |
| PETG- oder PLA-Filament | **1 Rolle** (der Ring braucht nur ein paar Gramm) | PETG oder PLA in **Schwarz** (oder sehr dunkel), **blickdicht**. | Eine helle oder durchscheinende Farbe lässt Infrarot durch die Wände und blendet den Sensor in der Sonne. **Schwarz und blickdicht**, kein „transparent“ und kein „Silk“. | Der [IR-Ring](https://github.com/Karnak19/bulloader-plus/tree/main/cad) und sein Teststück (`fit_coupon`). |

Die Druckdateien und wie man sie anpasst, liegen im Ordner
[`cad/`](https://github.com/Karnak19/bulloader-plus/tree/main/cad) des Repos.

## Werkzeug

| Werkzeug | Unverzichtbar? | Warum |
| -------- | -------------- | ----- |
| Multimeter | **Ja** | Den Wandler auf 5,0 V einstellen, bevor der ESP32 angeschlossen wird. Ohne Multimeter kein Aufbau. Dient auch zum Kalibrieren der Akkumessung. |
| Lötkolben, Lötzinn, Flussmittel | Ja | Alle Verbindungen. Ein temperaturgeregelter Lötkolben ist viel angenehmer. |
| Messschieber | Ja | Den Durchmesser des Auslaufrohrs (*Inner Barrel*) und der IR-Bauteile messen, um den Ring anzupassen. Ein günstiger digitaler reicht. |
| **1,5-mm**-Bohrer (mit Handbohrer/Stiftenklöbchen oder einer kleinen Bohrmaschine) | Ja, sehr wahrscheinlich | Das Auslaufrohr ist vermutlich aus Metall und damit für Infrarot undurchlässig: Du musst **zwei Löcher** bohren, auf die Fenster des Rings ausgerichtet, damit der Strahl durchkommt. Der Strahl geht nicht durch die Mitte des Rohrs, sondern 2 mm daneben: Bohre mit dem festgeschraubten Ring, von einem Fenster zum anderen, er dient als Bohrlehre. |
| USB-C-**Datenkabel** | Ja | Den ESP32 flashen. Viele USB-C-Kabel können nur laden: Wenn das Board am Computer nicht auftaucht, probier ein anderes Kabel. |
| Abisolierzange, Seitenschneider | Ja | Die Litzen vorbereiten. |
| Heißluftföhn oder Feuerzeug | Praktisch | Den Schrumpfschlauch schrumpfen. |
| Crimpzange JST-XH / Dupont | Nur bei Crimpsteckern | Bei fertig gecrimpten Kabeln unnötig. |

## Wenn die Teile ankommen

Bevor du irgendetwas lötest:

1. **OLED-Display: die Reihenfolge der Pins ablesen** (Beschriftung auf der Platine). VCC und GND
   können gegenüber dem [Schaltplan](/bulloader-plus/de/cablage/#schaltplan) vertauscht sein.
   Notier sie dir.
2. **LED und Fototransistor: die Kennzeichnung 940 nm** auf den Beuteln prüfen und beide getrennt
   aufbewahren, damit sie nicht durcheinandergeraten (sie sehen sich ähnlich).
3. **Wandler: mit dem Multimeter auf 5,0 V einstellen, ESP32 abgeklemmt**, vor allem anderen.
   Siehe [Erste Inbetriebnahme](/bulloader-plus/de/cablage/#erste-inbetriebnahme).
4. **Den Durchmesser des Auslaufrohrs messen**, mit dem Messschieber an der Stelle, wo der Ring
   sitzen wird, dazu den Körper der LED und des Fototransistors. Die Werte in
   [`cad/params.py`](https://github.com/Karnak19/bulloader-plus/blob/main/cad/params.py) eintragen.
5. **Das Teststück drucken** (`fit_coupon`), um das richtige Spiel zu finden, wie im
   [README des Ordners `cad/`](https://github.com/Karnak19/bulloader-plus/tree/main/cad#fit_coupon)
   beschrieben, bevor du den Ring druckst.

Danach geht es an die [Verkabelung](/bulloader-plus/de/cablage/).
