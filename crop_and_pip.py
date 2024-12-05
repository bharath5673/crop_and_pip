import cv2
import numpy as np



def picture_in_picture(main_image, overlay_image, pt1, pt2, img_ratio=3, border_size=3, x_margin=30, y_offset_adjust=-100):
    x1, y1 = pt1
    x2, y2 = pt2
    dash_length = 10
    thickness = 1
    main_image_ = main_image.copy()

    # Resize the overlay image to 1/img_ratio of the main image height
    new_height = main_image.shape[0] // img_ratio
    new_width = int(new_height * (overlay_image.shape[1] / overlay_image.shape[0]))
    overlay_resized = cv2.resize(overlay_image, (new_width, new_height))

    # Add a white border to the overlay image
    overlay_with_border = cv2.copyMakeBorder(
        overlay_resized,
        border_size, border_size, border_size, border_size,
        cv2.BORDER_CONSTANT, value=[255, 255, 255]
    )

    # Determine overlay position
    x_offset = main_image.shape[1] - overlay_with_border.shape[1] - x_margin
    y_offset = (main_image.shape[0] // 2) - overlay_with_border.shape[0] + y_offset_adjust

    # Draw dashed lines from ROI corners to PIP corners
    roi_corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
    pip_corners = [
        (x_offset, y_offset),  # Top-left corner of PIP
        (x_offset + overlay_with_border.shape[1], y_offset),  # Top-right
        (x_offset, y_offset + overlay_with_border.shape[0]),  # Bottom-left
        (x_offset + overlay_with_border.shape[1], y_offset + overlay_with_border.shape[0])  # Bottom-right
    ]

    # Draw dashed lines between corresponding corners
    for (roi_corner, pip_corner) in zip(roi_corners, pip_corners):
        # Calculate total distance and direction vectors
        distance = int(np.sqrt((pip_corner[0] - roi_corner[0]) ** 2 + (pip_corner[1] - roi_corner[1]) ** 2))
        direction = ((pip_corner[0] - roi_corner[0]) / distance, (pip_corner[1] - roi_corner[1]) / distance)
        
        # Draw dashes along the line
        for i in range(0, distance, dash_length * 2):
            start = (int(roi_corner[0] + direction[0] * i), int(roi_corner[1] + direction[1] * i))
            end = (int(roi_corner[0] + direction[0] * (i + dash_length)), int(roi_corner[1] + direction[1] * (i + dash_length)))
            cv2.line(main_image, start, end, (100,100,100), thickness)

    # Overlay the image (PIP)
    main_image[y_offset:y_offset + overlay_with_border.shape[0], x_offset:x_offset + overlay_with_border.shape[1]] = overlay_with_border

    # Replace the ROI in main_image with the original image piece (crop it from the original image)
    main_image[y1:y2, x1:x2] = main_image_[y1:y2, x1:x2]  # Replace the ROI with the original image section

    # Draw rectangle around the ROI
    cv2.rectangle(main_image, (x1, y1), (x2, y2), (0,0,255), thickness)

    return main_image




# Path to the video file
video_path = "FUEGO Volcano ERUPTS in Shocking Display of Nature's Fury - 8K Ultra HD Pure Quality - 8K Ultra HD Pure Quality (1080p60, h264, youtube).mp4"

# Create a video capture object
cap = cv2.VideoCapture(video_path)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4 format
out = cv2.VideoWriter('output_video.mp4', fourcc, fps, (frame_width, frame_height))




# Check if the video file is opened successfully
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

# Initialize variables for mouse callback
drawing = False  # True when the mouse button is pressed
ix, iy = -1, -1  # Initial x, y positions
roi_coords = []  # To store crop coordinates

# Mouse callback function
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, roi_coords

    if event == cv2.EVENT_LBUTTONDOWN:  # Mouse click down
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:  # Mouse drag
        if drawing:
            frame_copy = frame.copy()
            cv2.rectangle(frame_copy, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.imshow('Video Frame', frame_copy)

    elif event == cv2.EVENT_LBUTTONUP:  # Mouse release
        drawing = False
        roi_coords = [(ix, iy), (x, y)]
        print(f"ROI selected: {roi_coords}")

# Set the mouse callback
cv2.namedWindow('Video Frame')
cv2.setMouseCallback('Video Frame', draw_rectangle)

while cap.isOpened():
    ret, frame = cap.read()
    frame_ = frame.copy()
    
    if not ret:
        print("Reached end of video or error reading frame.")
        break
    
    if len(roi_coords) == 2:
        # Extract ROI using the coordinates
        x1, y1 = roi_coords[0]
        x2, y2 = roi_coords[1]
        cropped_roi = frame[min(y1, y2):max(y1, y2), min(x1, x2):max(x2, x1)]
        
        # Display the cropped ROI within the frame (Picture-in-Picture)
        if cropped_roi.size != 0:
            h, w = cropped_roi.shape[:2]
            frame[0:h, 0:w] = cropped_roi  # Placing ROI in the top-left corner

            frame = picture_in_picture(frame_, cropped_roi, pt1= roi_coords[0], pt2= roi_coords[1])

    # Display the frame
    cv2.imshow('Video Frame', frame)
    out.write(frame)
    
    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture object and close display window
cap.release()
out.release()
cv2.destroyAllWindows()
