# IoT 影像辨識自走車（B05）

樹莓派上跑 TensorFlow Lite 物件偵測，依偵測結果控制自走車，並把辨識記錄寫進 SQLite、用網頁呈現。

## 結構

| 目錄 | 內容 |
|---|---|
| `src/` | 主程式與硬體模組 |
| `web/` | Flask 後端 + 前端頁面 |
| `model/` | TFLite 模型（原檔名 `detect (24).tflite`） |
| `docs/` | 流程圖（期末報告因含組員個資未收錄） |
| `legacy/` | 開發過程的舊版本，見下方說明 |

### `src/`

- `detect_2.py` — 主程式：讀 Picamera 影像 → TFLite 推論 → 依結果驅動馬達、播語音、寫 SQLite
- `pcar.py` — 馬達 PWM 控制
- `distance.py` — 超音波測距（HC-SR04，trigger GPIO23 / echo GPIO24）
- `led.py` — LED 指示燈
- `tts.py` — 語音播報

### `web/`

- `SQLite_html.py` — Flask 後端，讀 SQLite 記錄（`port=8080`）
- `index.html` — 前端頁面

## 執行環境

樹莓派 + Picamera + HC-SR04 超音波模組 + 馬達驅動板。需要 `tflite_runtime`、`opencv-python`、`RPi.GPIO`、`flask`。

## `legacy/` 說明

開發中期的版本，**跑不起來**，缺 `pwm_motor.py` 與 `utils.py`（TensorFlow models repo 的 `object_detection/utils`）。留著只是保留過程。

其中 `car.py`、`object.py`、`pmodel.py` 的原始作者是 **Evan Juras**（Picamera + TensorFlow 物件偵測範例），`detect_change*.py` 則改寫自 [TensorFlow examples 的 Raspberry Pi 物件偵測範例](https://github.com/tensorflow/examples/tree/master/lite/examples/object_detection/raspberry_pi)。原始出處註解都保留在各檔案開頭。
