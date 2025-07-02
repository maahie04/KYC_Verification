import cv2
import numpy as np
from pynput import mouse

# Global variables that need to be shared
signature_canvas = np.ones((400, 600, 3), dtype=np.uint8) * 255
current_position = None
prev_position = None
capturing = False
last_drawn_point = None

def on_move(x, y):
    global current_position
    current_position = (x, y)

def on_click(x, y, button, pressed):
    global capturing, prev_position, last_drawn_point
    if button == mouse.Button.left:
        capturing = pressed
        if pressed:
            prev_position = (x, y)
            last_drawn_point = (x, y)
        else:
            prev_position = None
            last_drawn_point = None

def signcap():
    global signature_canvas, current_position, prev_position, capturing, last_drawn_point
    
    # Reset canvas and variables
    signature_canvas = np.ones((400, 600, 3), dtype=np.uint8) * 255
    current_position = None
    prev_position = None
    capturing = False
    last_drawn_point = None
    
    window_name = "Signature Capture"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 
    cv2.resizeWindow(window_name, 600, 400)

    listener = mouse.Listener(on_move=on_move, on_click=on_click)
    listener.start()

    print("Sign on your touchpad (left-click to start, release to finish)")
    while True:
        display_frame = signature_canvas.copy()
    
        cv2.putText(display_frame, "Draw signature - Press 's' to save, 'q' to quit, 'c' to clear", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
        if current_position:
            cv2.circle(display_frame, current_position, 3, (0, 0, 255), -1)
    
        if capturing and current_position and prev_position:
            dx = current_position[0] - prev_position[0]
            dy = current_position[1] - prev_position[1]
        
            if abs(dx) > 2 or abs(dy) > 2:
                if last_drawn_point:
                    cv2.line(signature_canvas, last_drawn_point, 
                            (last_drawn_point[0] + dx, last_drawn_point[1] + dy), 
                            (0, 0, 0), 2)
                else:
                    cv2.circle(signature_canvas, current_position, 2, (0, 0, 0), -1)
            
                last_drawn_point = (last_drawn_point[0] + dx, last_drawn_point[1] + dy) if last_drawn_point else current_position
                prev_position = current_position
    
        cv2.imshow(window_name, display_frame)
    
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            output_path = "captured_signature.png"
            cv2.imwrite(output_path, signature_canvas)
            print(f"Signature saved to {output_path}")
            break
        elif key == ord('q'):
            print("Signature capture cancelled")
            break
        elif key == ord('c'):
            signature_canvas = np.ones((400, 600, 3), dtype=np.uint8) * 255
            last_drawn_point = None  # Also reset drawing history when clearing

    listener.stop()
    cv2.destroyAllWindows()

    try:
        saved_img = cv2.imread("captured_signature.png")
        if saved_img is not None:
            cv2.imshow("Saved Signature", saved_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    except:
        pass

# Now you can call the function
#signcap()