import network
from umqtt.simple import MQTTClient
from machine import Pin, ADC, PWM, reset
from time import sleep

# 🔹 Configuración de MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "ESP32_LDR"
MQTT_TOPIC = "gds0652/lmlc"
MQTT_PORT = 1883

# 🔹 Configuración del sensor LDR y LED
ldr = ADC(Pin(34))  # Pin del sensor de luz
ldr.atten(ADC.ATTN_11DB)  # Rango de 0 a 3.3V
led = PWM(Pin(16), freq=1000)  # Salida PWM para el LED

# 🔹 Conexión a WiFi
def conectar_wifi():
    print("Conectando a WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Armando', 'Hola1234')
    intentos = 0
    while not sta_if.isconnected():
        print(".", end="")
        sleep(0.5)
        intentos += 1
        if intentos > 20:
            print("\n No se pudo conectar a WiFi. Reiniciando...")
            sleep(2)
            reset()
    print("\n WiFi Conectada!")

# 🔹 Conectar al broker MQTT
def conecta_broker():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60)
        client.connect()
        print("Conectado a MQTT y publicando en:", MQTT_TOPIC)
        return client
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return None

# 🔹 Conectar a WiFi
conectar_wifi()

# 🔹 Conectar al broker MQTT
client = None
while client is None:
    client = conecta_broker()
    if client is None:
        print("Reintentando conexión a MQTT en 5 segundos...")
        sleep(5)

# 🔹 Ciclo principal para leer la luz, ajustar el LED y enviar el nivel de luz
while True:
    try:
        valor_ldr = ldr.read()  # Leer ADC (0-4095)
        nivel_luz = 10 - int(valor_ldr / 4095 * 10)  # Invertir la escala de 1 a 10
        brillo = int(nivel_luz / 10 * 65535)  # Ajustar brillo LED

        led.duty_u16(brillo)  # Controlar el brillo del LED

        # Publicar valor en MQTT
        client.publish(MQTT_TOPIC, str(nivel_luz))
        
        # Imprimir solo el nivel de luz
        print(f"📤 Nivel de luz: {nivel_luz}")

    except Exception as e:
        print(f"Error MQTT: {e}. Reintentando conexión...")
        client = None
        while client is None:
            client = conecta_broker()
            if client is None:
                print(" Reintentando en 5 segundos...")
                sleep(5)

    sleep(1)
