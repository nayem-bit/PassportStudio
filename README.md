# Passport Photo Maker Studio V0.3

A powerful and easy-to-use tool for creating professional passport photos with advanced features like face detection, background removal, and more.

---

## Features

- **Face Detection and Cropping**
  Automatically detects and crops the largest face for accurate passport photo creation.

- **Background Removal**
  Remove backgrounds with one click and replace them with a solid color (default: sky blue).

- **Customizable Sizes**
  - Passport size (413x531px).
  - Application sizes (200x200px and 300x300px).

- **Denoising**
  - Option to remove noise or grain from images with adjustable intensity.

- **Image Upscaling**
  - Upscale images 2x to 8x for enhanced quality.

- **PDF Export**
  - Save processed images as a PDF with four photos arranged for A4 printing.

- **Drag-and-Drop Support**
  - Quickly load images by dragging and dropping them into the application.

- **Progress Indicators**
  - Visual progress bar with status updates during processing.

---

## What's New in V0.3

1. **Face Detection and Cropping**
   - Automatically detects and crops the largest face using OpenCV's Haar Cascade.

2. **Denoising Feature**
   - Added an option to remove grain/noise with adjustable intensity.

3. **PDF Export**
   - Generates a PDF with four images arranged for printing on A4 paper.

4. **Drag-and-Drop Support**
   - Quickly load images by dragging and dropping them into the app.

5. **Custom Resizing Options**
   - New presets for resizing to passport size (413x531px) and application sizes (200x200px, 300x300px).

6. **Progress Indicators**
   - Added a visual progress bar and text updates during processing.

7. **Enhanced Background Removal**
   - Improved background removal with customizable replacement color.

8. **Adjustable Upscaling**
   - Added a slider for upscaling images from 2x to 8x.

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/nayem121/Passport-Photo.git
   ```

2. Navigate to the project directory:
   ```bash
   cd Passport-Photo
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python PassportPhoto.py
   ```

---

## Dependencies

- Python 3.8+
- OpenCV
- NumPy
- Pillow
- rembg
- FPDF
- tkinterdnd2

Install all dependencies with the provided `requirements.txt` file.

---

## Usage

1. Launch the application.
2. Load an image by selecting a file or dragging and dropping it into the app.
3. Adjust the settings as needed (e.g., remove background, upscale, resize).
4. Click "Process" to apply changes.
5. Save the processed image or export it as a PDF.

---

## License

This project is licensed under the MIT License.

---

## Credits

Developed by Nayem Uddin Chowdhury. Visit [GitHub](https://github.com/nayem121) for more projects and updates.

