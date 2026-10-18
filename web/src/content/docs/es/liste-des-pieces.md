---
title: Lista de piezas
description: Todo lo que hay que pedir para montar un BULLOADER+, con las trampas que evitar al elegir cada pieza.
---

Esta página es una lista de la compra. Todo se encuentra en tiendas de electrónica en línea
(AliExpress y similares). Aquí no hay enlaces ni precios, cambian demasiado rápido: en su lugar
tienes **términos de búsqueda** para copiar y pegar y, sobre todo, **lo que hay que comprobar en la
ficha del producto** antes de pulsar «comprar». Los términos de búsqueda están en inglés a
propósito: es lo que mejor funciona en esas tiendas.

Los valores (resistencias, condensadores, pines) son los de la página
[Cableado](/bulloader-plus/es/cablage/). Si algún día las dos páginas no coinciden, manda la de
cableado y, por encima de ella,
[`firmware/src/config.h`](https://github.com/Karnak19/bulloader-plus/blob/main/firmware/src/config.h).

Las cantidades propuestas incluyen algo de margen: estas piezas cuestan de unos céntimos a unos
pocos euros, y esperar tres semanas un segundo envío por un LED estropeado sale mucho más caro.

## Antes de pedir: la tensión del servo

:::danger[Comprueba tu servo antes de hacer el pedido]
El servo original del BULLOADER va conectado **directamente a la batería 2S**, que llega a
**8,4 V** cuando está cargada. Muchos servos «35 kg» solo están especificados para **4,8 a
6,8 V**: por encima, se calientan y acaban quemándose. Solo los servos llamados **HV** (*high
voltage*) aceptan 8,4 V.

1. Busca la referencia impresa en la etiqueta del servo y consulta su hoja de datos.
2. **Si su rango de tensión llega hasta 8,4 V (servo HV)**: no hay que añadir nada, sigue
   conectado a la batería.
3. **Si no**, añade al pedido un **BEC** (un pequeño regulador de aeromodelismo) o un segundo
   convertidor, solo para el servo. Lo que hay que mirar:
   - **la corriente**: como mínimo la **corriente de bloqueo** del servo (*stall current*, lo que
     consume cuando hace fuerza estando bloqueado, en la hoja de datos). Para uno de 35 kg, cuenta
     con varios amperios: busca **5 A en continuo o más**;
   - **la tensión de salida**: dentro del rango del servo, por ejemplo **6,0 V** para un servo de
     4,8–6,8 V. Los UBEC de aeromodelismo suelen tener un puente (*jumper*) 5 V / 6 V;
   - **la entrada**: compatible con 2S (7,4 V, 8,4 V cargada).

   Términos de búsqueda: «UBEC 5A 6V», «UBEC 2-6S 5A».

**Un MP1584 no basta para el servo.** El de la lista solo alimenta el ESP32: aguanta unos 3 A de
pico, mucho menos de lo que consume un servo grande bloqueado.
:::

Si añades un BEC, el condensador de 470 µF va a su salida, lo más cerca posible del servo.

## Lo que ya tienes

Estas piezas vienen del BULLOADER original y se reutilizan. **No las pidas.**

| Pieza                          | Cantidad | Estado       | Para qué sirve                                                                                  |
| ------------------------------ | -------- | ------------ | ----------------------------------------------------------------------------------------------- |
| Batería LiPo 2S (7,4 V)        | 1        | ya la tienes | Lo alimenta todo. Su cargador LiPo, también.                                                    |
| Servo 35 kg 360° (rotación continua) | 1  | ya lo tienes | Mueve el mecanismo. Mira el recuadro de arriba sobre su tensión.                                |
| Interruptor de encendido       | 1        | ya lo tienes | Corte general, entre la batería y todo lo demás.                                                |
| Botón (el antiguo botón de 12 V) | 1      | ya lo tienes | Pasa a ser el botón **GO**: un simple contacto entre GPIO 4 y masa, desconectado del antiguo 12 V. |

## Electrónica principal

| Pieza | Cantidad a pedir | Especificación exacta | Lo que importa al elegir | Para qué sirve |
| ----- | ---------------- | --------------------- | ------------------------ | -------------- |
| ESP32-C3 SuperMini | **3** (1 en uso + 2 de repuesto) | Placa ESP32-**C3** «SuperMini», USB-C, unos 22 × 18 mm. Búsqueda: «ESP32-C3 SuperMini». | Que sea **C3**: hay placas «SuperMini» con S3, C6 o H2, que no sirven para este firmware ni este patillaje. Algunos lotes tienen una antena floja (poco alcance Bluetooth): comprar varias permite quedarse con la mejor. Son baratas. Las tiras de pines suelen venir aparte, sin soldar. | El cerebro: cuenta las bolas y controla el servo, la pantalla y el Bluetooth. |
| Convertidor reductor MP1584 | **2** (1 + 1 de repuesto) | Módulo MP1584**EN**, unos 22 × 17 mm, entrada hasta ~28 V, ~3 A de pico. Mejor la versión de **salida fija de 5 V**; si no, la **regulable** (con un pequeño tornillo de potenciómetro). Búsqueda: «MP1584EN 5V fixed output» o «MP1584EN step down adjustable». | La versión de **5 V fija** es la más segura: no hay nada que ajustar, así que no hay tornillo que girar mal. Una regulable también vale, pero sale de fábrica con una tensión cualquiera, a veces cercana a la de la batería: **hay que** ajustarla a 5,0 V con el multímetro. En los dos casos, **mide la salida con el multímetro antes de conectar el ESP32**. No cojas otro módulo en su lugar: el «Mini-360», por ejemplo, usa otro chip. | Da los 5 V del ESP32 a partir de la batería. No alimenta el servo. |

## Sensor infrarrojo

| Pieza | Cantidad a pedir | Especificación exacta | Lo que importa al elegir | Para qué sirve |
| ----- | ---------------- | --------------------- | ------------------------ | -------------- |
| LED infrarrojo de 3 mm | **1 bolsa** (de 10 a 50 unidades, necesitas 1) | LED emisor IR, encapsulado de **3 mm**, **940 nm**. Búsqueda: «3mm IR LED 940nm emitter». | La **longitud de onda**: **940 nm**, la misma que el fototransistor. Es el error más frecuente: un LED de 850 nm (brilla en rojo oscuro) con un sensor de 940 nm, o al revés, da una señal débil e inestable. Encapsulado de 3 mm, no de 5 mm: el collar está diseñado para 3 mm. | Emite el haz que cortan las bolas. |
| Fototransistor de 3 mm | **1 bolsa** (de 10 a 50 unidades, necesitas 1) | Fototransistor NPN, encapsulado de **3 mm**, **940 nm**, 2 patas. Mejor con **epoxi oscuro** (negro o violeta muy oscuro). Búsqueda: «3mm phototransistor 940nm black». | **940 nm**, como el LED. El epoxi **oscuro** filtra la luz visible: menos problemas a pleno sol, así que es preferible. Cuidado con los parecidos: un «receptor IR» de **3 patas** (VS1838B, TSOP…) es un receptor de mando a distancia y aquí no funciona. Un fotodiodo es idéntico a simple vista, pero da una señal mucho más débil: la ficha tiene que decir *phototransistor*. | Ve el haz y, por tanto, cada bola que pasa. |

## Controles

| Pieza | Cantidad a pedir | Especificación exacta | Lo que importa al elegir | Para qué sirve |
| ----- | ---------------- | --------------------- | ------------------------ | -------------- |
| Encoder rotativo KY-040 | **2** (1 + 1 de repuesto) | Módulo **KY-040**: encoder con pasos y pulsador, montado en su pequeña placa con sus resistencias de pull-up, 5 pines (CLK, DT, SW, +, GND). Búsqueda: «KY-040 rotary encoder module». | Coge el **módulo en placa**, no el encoder suelto. Se conecta a **3,3 V** (no a 5 V), mira el [cableado](/bulloader-plus/es/cablage/). Si un paso avanza 2 en lugar de 1 (o al revés), se ajusta en `config.h`, no hace falta devolver el módulo. | Ajustar el número de bolas y confirmar con un clic. |
| Mando para el encoder | **2** | Mando para eje de **6 mm**, de diámetro grande (25 mm o más), moleteado o de goma. Búsqueda: «knob 6mm shaft knurled». | Mira el eje de tu KY-040: **estriado** (con ranuras alrededor) o **en D** (con una cara plana). El mando tiene que ser para el mismo tipo. Grande y moleteado para usarlo **con guantes**. Algunos KY-040 vienen con un mando pequeño, normalmente demasiado pequeño. | Girar el mando en el campo. |
| Pantalla OLED de 0,96" | **2** (1 + 1 de repuesto) | OLED de **0,96"**, **128 × 64**, controlador **SSD1306**, interfaz **I2C de 4 pines** (VCC, GND, SCL, SDA). Búsqueda: «0.96 OLED SSD1306 I2C 4 pin 128x64». | **4 pines, I2C.** Las versiones de **7 pines** (SPI) no sirven. **El orden VCC / GND cambia según el vendedor** (GND-VCC-SCL-SDA o VCC-GND-SCL-SDA): lee la serigrafía antes de soldar, invertirlos quema la pantalla. Dirección I2C **0x3C** casi siempre, a veces **0x3D**. Mejor de un solo color (blanco o azul): las «amarillo/azul» tienen una franja amarilla fija arriba. | Mostrar el estado, la cuenta y la batería. |

## Componentes pasivos

| Pieza | Cantidad a pedir | Especificación exacta | Lo que importa al elegir | Para qué sirve |
| ----- | ---------------- | --------------------- | ------------------------ | -------------- |
| Condensador de 470 µF | **5** (necesitas 1) | Electrolítico de **470 µF**, **16 V o más**. Búsqueda: «470uF 16V electrolytic capacitor». | La tensión: **16 V como mínimo** (uno de 25 V también vale, solo es algo más grande). Uno de 10 V o 6,3 V no aguanta los 8,4 V de la batería. Tiene **polaridad**: la pata `−` está marcada con una franja en el cuerpo. | En la alimentación del servo, lo más cerca posible de él: evita las caídas de tensión cuando arranca el servo. |
| Condensador de 100 nF | **10** (necesitas 1) | Cerámico de **100 nF** (marcado «104»), 50 V. Búsqueda: «100nF 104 ceramic capacitor». | Nada complicado. Suele venderse en paquetes de 50 o 100, es normal. | Entre GPIO 0 y masa: suaviza la lectura de la batería. |
| Resistencia de 220 Ω | en el kit (necesitas 1) | 220 Ω, 1/4 W. | | En serie con el LED IR (unos 10 mA). |
| Resistencia de 10 kΩ | en el kit (necesitas 1) | 10 kΩ, 1/4 W. | | Pull-up del fototransistor a 3,3 V. |
| Resistencia de 100 kΩ | en el kit (necesitas 1) | 100 kΩ, 1/4 W. | | Divisor de tensión de la batería, lado batería. |
| Resistencia de 20 kΩ | en el kit (necesitas 1) | 20 kΩ, 1/4 W. | **20 kΩ** exactamente: el firmware calcula la tensión de la batería con 100 kΩ / 20 kΩ. A 8,4 V, el pin del ESP32 ve entonces 1,40 V. | Divisor de tensión de la batería, lado masa. |
| Kit de resistencias | **1** | Surtido de resistencias de película metálica de 1/4 W, 1 %, con **220 Ω, 10 kΩ, 20 kΩ y 100 kΩ**. Búsqueda: «metal film resistor kit 1/4W 1%». | Lo más sencillo: un kit cubre los cuatro valores y te servirá más adelante. Comprueba en la lista de valores del kit que esté **20 kΩ** (los kits habituales de 30 valores lo traen). Una de **1 MΩ** en el kit también viene bien si el receptor IR resulta ser un fotodiodo y no un fototransistor. | Todas las resistencias de arriba. |

## Cableado y tornillería

| Pieza | Cantidad a pedir | Especificación exacta | Lo que importa al elegir | Para qué sirve |
| ----- | ---------------- | --------------------- | ------------------------ | -------------- |
| Placa perforada | **1 lote** (de 5 a 10 placas) | Placa de prototipos con pads, paso de **2,54 mm**, doble cara, de 5 × 7 cm (para recortar). Búsqueda: «PCB prototype board double sided 5x7». | Con pads (uno por agujero), no con tiras. Doble cara: los pads aguantan mejor. Las medidas exactas del soporte de la electrónica llegarán más adelante: una placa de 5 × 7 cm se recorta fácilmente. | Sostener el ESP32, el convertidor y los componentes pequeños. |
| Tira de pines hembra de 2,54 mm | **1 lote** | Tiras de pines hembra divisibles, paso de 2,54 mm. Búsqueda: «female pin header 2.54mm». | Permite enchufar el ESP32 en lugar de soldarlo: se cambia en dos segundos. | Zócalo del ESP32 en la placa. |
| Cable de silicona grueso | **1 m** rojo + **1 m** negro | Cable de silicona flexible de **18 AWG** (unos 0,8 mm²). Búsqueda: «silicone wire 18AWG». | Silicona: flexible y no se derrite con el soldador. Lo bastante grueso para la **corriente del servo**, que se mide en amperios. | Batería, interruptor, servo (o BEC), entrada del convertidor. |
| Cable fino para señales | **1 lote** (varios colores) | Cable de silicona de **26 o 28 AWG**, varios colores. Búsqueda: «silicone wire 26AWG 10 colors». | Varios colores para no confundirse (un color por función). La silicona se dobla bien en una caja estrecha. | LED IR, fototransistor, encoder, pantalla, botón GO, señal del servo. |
| Conectores JST-XH de 2,54 mm | **1 kit** (2, 3, 4 y 5 pines) | Kit JST-XH de 2,54 mm: bases para soldar y clavijas. Lo más fácil: **cables ya crimpados**. Búsqueda: «JST XH 2.54 pre-crimped cable» o «JST XH connector kit». | Para poder **desconectar** cada pieza (pantalla, encoder, sensor IR, botón) y desmontar sin desoldar. Las clavijas para crimpar necesitan una crimpadora: los cables ya crimpados te la ahorran. Los Dupont también sirven, pero aguantan peor las vibraciones. **No para la corriente del servo**: para él, deja su conector original. | Conectar la electrónica a la placa. |
| Tornillo M3 × 10 | **1 lote** (necesitas 2) | Tornillo **M3 × 10 mm**, cabeza cilíndrica con hexágono interior (Allen). Búsqueda: «M3 x 10 socket head screw». | Longitud de **10 mm**. Un surtido M3 de 6 a 20 mm también servirá para lo siguiente (soporte de la electrónica). | Aprieta el collar IR sobre el tubo, un tornillo por mitad. |
| Tuerca M3 | **1 lote** (necesitas 2) | Tuerca hexagonal **M3** estándar (5,5 mm entre caras, 2,4 mm de grosor). Búsqueda: «M3 hex nut». | Tuerca hexagonal normal, ni con brida ni autoblocante de nailon: tiene que entrar en su alojamiento hexagonal del collar. | Alojada en el collar IR, frente a cada tornillo. |
| Funda termorretráctil negra | **1 surtido** | Funda termorretráctil **negra**, diámetros de 1,5 a 6 mm. Búsqueda: «heat shrink tube black assortment». | **Negra**: además de aislar las soldaduras, protege de la luz la parte trasera del fototransistor. | Aislar las soldaduras y tapar de la luz el fototransistor y sus patas. |

## Impresión

| Pieza | Cantidad a pedir | Especificación exacta | Lo que importa al elegir | Para qué sirve |
| ----- | ---------------- | --------------------- | ------------------------ | -------------- |
| Filamento PETG o PLA | **1 bobina** (el collar solo usa unos gramos) | PETG o PLA **negro** (o muy oscuro), **opaco**. | Un color claro o translúcido deja pasar el infrarrojo a través de las paredes y deslumbra al sensor al sol. **Negro opaco**, nada de «transparente» ni «silk». | El [collar IR](https://github.com/Karnak19/bulloader-plus/tree/main/cad) y su pieza de prueba (`fit_coupon`). |

Los archivos para imprimir y cómo ajustarlos están en la carpeta
[`cad/`](https://github.com/Karnak19/bulloader-plus/tree/main/cad) del repositorio.

## Herramientas

| Herramienta | ¿Imprescindible? | Por qué |
| ----------- | ---------------- | ------- |
| Multímetro | **Sí** | Ajustar el convertidor a 5,0 V antes de conectar el ESP32. Sin multímetro, no hay montaje. También sirve para calibrar la lectura de la batería. |
| Soldador, estaño, flux | Sí | Todas las conexiones. Un soldador con temperatura regulable es mucho más cómodo. |
| Pie de rey | Sí | Medir el diámetro del tubo de salida (*inner barrel*) y de los componentes IR, para ajustar el collar. Basta con uno digital barato. |
| **Cortatubos** (lo mejor) o sierra de arco en una caja de ingletes, y un **desbarbador** | Sí | El tubo de salida es de metal y, por tanto, opaco al infrarrojo. No se taladra: se corta en dos, el collar sujeta las dos mitades una frente a otra y el haz pasa por el hueco entre ellas. El cortatubos da un corte a escuadra sin esfuerzo. El desbarbador (o una broca avellanadora girada a mano) limpia los extremos cortados. Mira [más abajo](#cortar-el-tubo-y-montar-el-collar). |
| Cable USB-C **de datos** | Sí | Flashear el ESP32. Muchos cables USB-C solo cargan: si la placa no aparece en el ordenador, prueba con otro cable. |
| Pelacables, alicate de corte | Sí | Preparar los cables. |
| Pistola de aire caliente o mechero | Práctico | Contraer la funda. |
| Crimpadora JST-XH / Dupont | Solo con clavijas para crimpar | Innecesaria con cables ya crimpados. |

## Al recibir las piezas

Antes de soldar nada:

1. **Pantalla OLED: lee el orden de los pines** en la serigrafía (VCC y GND pueden estar invertidos
   respecto al [esquema](/bulloader-plus/es/cablage/#esquema-de-cableado)). Apúntalo.
2. **LED y fototransistor: comprueba la marca 940 nm** en las bolsas y guárdalos por separado para
   no mezclarlos (se parecen).
3. **Convertidor: ajústalo a 5,0 V con el multímetro, con el ESP32 desconectado**, antes que nada.
   Mira el [primer encendido](/bulloader-plus/es/cablage/#primer-encendido).
4. **Mide el diámetro del tubo de salida** con el pie de rey, donde irá el collar, y también el
   cuerpo del LED y del fototransistor. Anota los valores en
   [`cad/params.py`](https://github.com/Karnak19/bulloader-plus/blob/main/cad/params.py).
5. **Imprime la pieza de prueba** (`fit_coupon`) para encontrar la holgura adecuada, como se explica
   en el [README de la carpeta `cad/`](https://github.com/Karnak19/bulloader-plus/tree/main/cad#fit_coupon),
   antes de imprimir el collar.

## Cortar el tubo y montar el collar

El infrarrojo no atraviesa el tubo de salida de metal. En vez de hacerle agujeros, se corta en
dos. El collar sujeta las dos mitades una frente a otra con un hueco de **6,5 mm** entre ellas, y
el haz pasa por ese hueco, a través del anillo impreso que guía las bolas.

1. **Marca** una franja de **6,5 mm** (`BARREL_GAP` en `params.py`) donde va a ir el collar. Es la
   longitud de tubo que hay que quitar: el collar devuelve justo ese hueco, así que una vez montado
   el tubo conserva su longitud original.
2. **Corta a escuadra** a cada lado de la franja (o corta una vez y luego acorta una de las mitades
   6,5 mm). Lo mejor es un **cortatubos**: corte recto y limpio, sin esfuerzo. Si no, una sierra de
   arco en una caja de ingletes.
3. **Desbarba** por dentro y por fuera. En el borde **interior** de cada extremo cortado, haz un
   **chaflán ligero**, con un desbarbador o una broca avellanadora girada a mano. La guía impresa
   mide 6,2 mm y el tubo 6,05 mm: sin ese chaflán, una bola puede engancharse en el pequeño escalón
   al entrar en la mitad de salida.
4. **Sopla** dentro de las dos mitades para sacar las virutas.
5. **Mete** cada mitad en el collar hasta que haga tope en el anillo del centro. El anillo fija el
   hueco y la alineación, no tú.
6. **Aprieta** los dos tornillos M3, uno por mitad.

Y después, al [cableado](/bulloader-plus/es/cablage/).
