# Motion-Based Security Camera

A lightweight security camera built with Python and OpenCV. It watches a webcam (or video file), detects movement using **background subtraction**, and saves timestamped screenshots only when something moves. Every event is logged to a CSV file.

**No machine learning model training. No paid APIs. Runs fully offline on a normal laptop.**

![Demo](demo.gif)

---

## Features

- Real-time motion detection using OpenCV's MOG2 background subtractor
- Green bounding boxes drawn around moving objects
- Timestamped screenshots saved only when motion occurs
- Cooldown timer to avoid saving hundreds of near-identical images
- CSV event log (timestamp, image file, number of regions, largest area)
- Optional short video clip recording with `--record`
- Works with a built-in webcam, an external camera, or a video file
- Adjustable sensitivity from the command line

---

## How It Works

1. **Capture:** each frame is read from the camera and resized to 640 px wide for speed.
2. **Preprocess:** the frame is converted to grayscale and blurred (Gaussian blur) to remove noise.
3. **Background subtraction:** the MOG2 algorithm learns what the static background looks like and produces a mask where moving pixels are white.
4. **Clean the mask:** shadows are thresholded out, small specks are removed with morphological opening, and gaps are filled with dilation.
5. **Find contours:** connected white regions are detected. Any region smaller than `--min-area` is ignored.
6. **Trigger events:** if at least one large region remains, the frame is marked as motion. A screenshot is saved (respecting the cooldown) and a row is added to `events.csv`.

The first 30 frames are used only to learn the background, so stay out of frame for the first second or two.

---

## Requirements

- Python 3.9 or newer
- A webcam (built-in laptop camera is fine) or any video file
- OpenCV

---

## Installation

```bash
git clone https://github.com/YOUR-USERNAME/motion-camera.git
cd motion-camera
pip install -r requirements.txt
```

Or install the dependency directly:

```bash
pip install opencv-python
```

---

## Usage

Run with the default webcam:

```bash
python motion_camera.py
```

Run on a video file:

```bash
python motion_camera.py --source video.mp4
```

Record short clips when motion is detected:

```bash
python motion_camera.py --record
```

Reduce false alarms by ignoring small movements:

```bash
python motion_camera.py --min-area 3000
```

Press **q** in the preview window to quit.

### Command-line options

| Option | Default | Description |
|---|---|---|
| `--source` | `0` | Camera index (0, 1, ...) or path to a video file |
| `--min-area` | `1500` | Minimum contour area to count as motion. Higher means less sensitive |
| `--cooldown` | `3.0` | Seconds between saved screenshots |
| `--out` | `motion_events` | Output folder |
| `--record` | off | Save short video clips on motion |
| `--clip-tail` | `3.0` | Seconds to keep recording after motion stops |
| `--no-preview` | off | Run without opening preview windows |

---

## Output

After running, a `motion_events` folder is created:

```
motion_events/
├── images/        # timestamped screenshots (motion_YYYYMMDD_HHMMSS.jpg)
├── clips/         # video clips (only with --record)
└── events.csv     # log of every motion event
```

Example `events.csv`:

| timestamp | image_file | motion_regions | largest_area |
|---|---|---|---|
| 2026-10-04 17:23:25 | motion_20261004_172325.jpg | 1 | 8420 |
| 2026-10-04 17:23:31 | motion_20261004_172331.jpg | 2 | 12310 |

---

## Project Structure

```
motion-camera/
├── motion_camera.py    # main script
├── requirements.txt    # dependencies
├── README.md
├── .gitignore
└── demo.gif            # demo recording
```

---

## Tuning Tips

- **Too many false alarms?** Increase `--min-area` (try 3000 to 5000).
- **Missing real movement?** Decrease `--min-area` (try 800 to 1000).
- **Camera not opening?** Try `--source 1`, close apps like Zoom or Teams that may be using the camera, and check Windows camera privacy settings.
- **Slow or black frames on Windows?** Use `cv2.VideoCapture(source, cv2.CAP_DSHOW)` in the script.

---

## Limitations

- Sudden lighting changes (lights switching on, clouds, screen flicker) can trigger false alarms.
- The camera must stay still. A moving camera makes the whole frame look like motion.
- It detects movement only. It does not identify what moved (person, pet, object).
- Very slow movement may be absorbed into the background over time.

---

## Future Improvements

- Region of interest to ignore parts of the frame (for example, a window with trees)
- Streamlit dashboard to browse events with date filters
- Chart of motion events per hour using pandas and matplotlib
- Sound or email alert when motion starts
- Optional pretrained person detection to reduce false alarms

---

## Tech Stack

- Python
- OpenCV (`cv2`)
- Standard library: `argparse`, `csv`, `datetime`, `os`, `time`

---

## Author

**Borra Tharun Thirupalu**

Built as a small project during the Kodacy x SPACE virtual internship in Artificial Intelligence and Machine Learning.

- GitHub: [YOUR-USERNAME](https://github.com/YOUR-USERNAME)
- LinkedIn: [your-profile](https://linkedin.com/in/your-profile)

---

## License

This project is released under the MIT License. Feel free to use and modify it.
