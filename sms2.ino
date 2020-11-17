#include <MKRGSM.h>

const char PINNUMBER[] = " ";
// APN data
const char GPRS_APN[] = "hologram";
const char GPRS_LOGIN[] = " ";
const char GPRS_PASSWORD[] = " ";
String HOLOGRAM_DEVICE_KEY = "KaAGs)hk";
int Temp1 = 9000;
int Temp2 = 10;
String HOLOGRAM_TOPIC1 = "Temperature1";


// initialize the library instance
GSMClient client;
GPRS gprs;
GSM gsmAccess;

// Hologram's Embedded API (https://hologram.io/docs/reference/cloud/embedded/) URL and port
char server[] = "cloudsocket.hologram.io";
int port = 9999;

void setup() {
  // initialize serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  Serial.println("Starting Arduino web client.");
  // connection state
  boolean connected = false;

  // After starting the modem with GSM.begin()
  // attach to the GPRS network with the APN, login and password
  while (!connected) {
     Serial.println("Begin gsm Access");
    //Serial.println(gsmAccess.begin()); //Uncomment for testing
    
    if ((gsmAccess.begin() == GSM_READY) &&
        (gprs.attachGPRS(GPRS_APN, GPRS_LOGIN, GPRS_PASSWORD) == GPRS_READY)) {
      connected = true;
      Serial.println("GSM Access Success");
    } 
    else {
      Serial.println("Not connected");
      delay(1000);
    }
  }

  Serial.println("connecting...");

  // if you get a connection, report back via serial:
  if (client.connect(server, port)) {
    Serial.println("connected");
    // Send a Message request:
    client.println("{\"k\":\"" + HOLOGRAM_DEVICE_KEY +"\",\"d\":\"" +Temp1+"\",\"t\":\""+HOLOGRAM_TOPIC1+"\"}");
  
  } else {
    // if you didn't get a connection to the server:
    Serial.println("connection failed");
  }
}

void loop() {
  // if there are incoming bytes available
  // from the server, read them and print them:
  if (client.available()) {
    char c = client.read();
    Serial.print(c);
  }

  // if the server's disconnected, stop the client:
  if (!client.available() && !client.connected()) {
    Serial.println();
    Serial.println("disconnecting.");
    client.stop();

    // do nothing forevermore:
    for (;;)
      ;
  }
}
