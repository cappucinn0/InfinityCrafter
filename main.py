import pygame
import sys
import game_logic

pygame.init()
pygame.mixer.init()

# Load sound effects
drag_sound = pygame.mixer.Sound("drag_sound.wav")
combine_sound = pygame.mixer.Sound("combine_sound.wav")

drag_sound.set_volume(0.5)
combine_sound.set_volume(0.5)

# If it's a class method
api_handler = game_logic.ElementCombiner(api_key="Your API Key")

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Element Drag & Combine")

# Colors and styles
WHITE = (255, 255, 255)
DARK = (30, 30, 30)
LIGHT = (240, 240, 240)
BLACK = (0, 0, 0)
HOVER_COLOR = (220, 220, 220)
BG_TOP = (100, 0, 150)
BG_BOTTOM = (25, 0, 75)
SCROLLBAR_COLOR = (150, 150, 150)
SCROLLBAR_HOVER_COLOR = (120, 120, 120)

# Double click settings
DOUBLE_CLICK_TIME = 500  # milliseconds

# Double-click handler class
class DoubleClickHandler:
    def __init__(self, double_click_time=500):
        self.double_click_time = double_click_time
        self.last_click_time = 0
        self.last_click_pos = (0, 0)
        self.click_tolerance = 10
        self.first_click_handled = False
        
    def check_double_click(self, current_time, mouse_pos):
        """Check if this is a double click and return True if so"""
        time_diff = current_time - self.last_click_time
        
        if time_diff < self.double_click_time:
            # Check position tolerance
            pos_diff = ((mouse_pos[0] - self.last_click_pos[0])**2 + 
                       (mouse_pos[1] - self.last_click_pos[1])**2)**0.5
            
            if pos_diff < self.click_tolerance:
                # This is a double click
                self.last_click_time = 0  # Reset to prevent triple clicks
                return True
        
        # Update for next potential double click
        self.last_click_time = current_time
        self.last_click_pos = mouse_pos
        return False

def duplicate_canvas_element(original_element, canvas_elements, screen_width, screen_height):
    """Duplicate a canvas element and find a safe position for it"""
    # Calculate new position with offset
    offset_x = 60
    offset_y = 20
    
    new_x = original_element["rect"].x + offset_x
    new_y = original_element["rect"].y + offset_y
    
    # Keep within screen bounds
    element_width = original_element["rect"].width
    element_height = original_element["rect"].height
    
    # Check right boundary
    if new_x + element_width > screen_width:
        new_x = original_element["rect"].x - offset_x
    
    # Check bottom boundary  
    if new_y + element_height > screen_height:
        new_y = original_element["rect"].y - offset_y
    
    # Check left boundary
    if new_x < 0:
        new_x = original_element["rect"].x + offset_x
    
    # Check top boundary
    if new_y < 0:
        new_y = original_element["rect"].y + offset_y
    
    # Create the duplicate
    duplicate = {
        "element": {"name": original_element["element"]["name"]},
        "rect": pygame.Rect(new_x, new_y, element_width, element_height)
    }
    
    canvas_elements.append(duplicate)
    return duplicate

def draw_canvas_element_with_effect(screen, elem, font, is_new_duplicate=False):
    """Draw canvas element with optional duplicate effect"""
    rect = elem["rect"]
    
    # Add a subtle glow effect for newly duplicated elements
    if is_new_duplicate:
        glow_rect = pygame.Rect(rect.x - 2, rect.y - 2, rect.width + 4, rect.height + 4)
        pygame.draw.rect(screen, (255, 255, 150), glow_rect, border_radius=14)
    
    pygame.draw.rect(screen, WHITE, rect, border_radius=12)
    label_surface = font.render(elem['element']['name'], True, BLACK)
    label_rect = label_surface.get_rect(center=rect.center)
    screen.blit(label_surface, label_rect)

# Initialize double-click handler
double_click_handler = DoubleClickHandler(DOUBLE_CLICK_TIME)

# Fonts
try:
    font = pygame.font.SysFont("Segoe UI Emoji", 20)  # Smaller font
    title_font = pygame.font.SysFont("Segoe UI Emoji", 24, bold=True)  # Smaller title font
except:
    font = pygame.font.Font(None, 20)
    title_font = pygame.font.Font(None, 24)

# UI dimensions
is_light_mode = True
mode_button_rect = pygame.Rect(20, 20, 180, 50)
SIDEBAR_WIDTH = 250
SIDEBAR_PADDING = 20
sidebar_rect = pygame.Rect(SCREEN_WIDTH - SIDEBAR_WIDTH - SIDEBAR_PADDING, SIDEBAR_PADDING,
                           SIDEBAR_WIDTH, SCREEN_HEIGHT - SIDEBAR_PADDING * 2)

# Scrollbar dimensions
SCROLLBAR_WIDTH = 15
scrollbar_rect = pygame.Rect(sidebar_rect.right - SCROLLBAR_WIDTH - 5, sidebar_rect.y + 60, 
                            SCROLLBAR_WIDTH, sidebar_rect.height - 70)

# Element definitions
elements = [
    {"name": "🔥Fire"},
    {"name": "💧Water"},
    {"name": "🌍Earth"},
    {"name": "💨Air"}
]
element_cache = set(el["name"] for el in elements)

# Smaller element dimensions
element_height = 45  # Reduced from 60
element_margin = 8   # Reduced from 10
scroll_offset = 0
max_scroll = 0

# Scrolling variables
scrolling = False
scroll_start_y = 0

# Track newly duplicated elements for visual effect
newly_duplicated = []
duplicate_effect_timer = 0

def calculate_max_scroll():
    global max_scroll
    total_height = len(elements) * (element_height + element_margin)
    visible_height = sidebar_rect.height - 70  # Account for title space
    max_scroll = max(0, total_height - visible_height)

def get_element_rects():
    rects = []
    start_y = sidebar_rect.y + 70 - scroll_offset
    visible_area = pygame.Rect(sidebar_rect.x, sidebar_rect.y + 60, 
                              sidebar_rect.width - SCROLLBAR_WIDTH - 10, 
                              sidebar_rect.height - 70)
    
    for i in range(len(elements)):
        rect = pygame.Rect(
            sidebar_rect.x + 15,
            start_y + i * (element_height + element_margin),
            SIDEBAR_WIDTH - 40,  # Account for scrollbar space
            element_height
        )
        # Only include rects that are visible
        if rect.colliderect(visible_area):
            rects.append((i, rect))
        else:
            rects.append((i, None))  # Element not visible
    return rects

def get_scrollbar_thumb_rect():
    if max_scroll <= 0:
        return None
    
    thumb_height = max(20, int((sidebar_rect.height - 70) * (sidebar_rect.height - 70) / (len(elements) * (element_height + element_margin))))
    thumb_y = scrollbar_rect.y + int((scroll_offset / max_scroll) * (scrollbar_rect.height - thumb_height))
    
    return pygame.Rect(scrollbar_rect.x, thumb_y, SCROLLBAR_WIDTH, thumb_height)

def handle_scroll(mouse_pos, scroll_direction):
    global scroll_offset
    if sidebar_rect.collidepoint(mouse_pos):
        scroll_speed = 30  # Pixels per scroll
        scroll_offset += scroll_direction * scroll_speed
        scroll_offset = max(0, min(scroll_offset, max_scroll))

dragging_element = None
drag_offset = (0, 0)
canvas_elements = []
clock = pygame.time.Clock()

def draw_gradient_background(surface, top_color, bottom_color):
    for y in range(SCREEN_HEIGHT):
        ratio = y / SCREEN_HEIGHT
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

# Calculate initial max scroll
calculate_max_scroll()

# Main loop
running = True
while running:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()
    element_rects = get_element_rects()

    # Update duplicate effect timer
    if newly_duplicated:
        duplicate_effect_timer += clock.get_time()
        if duplicate_effect_timer > 1000:  # Effect lasts 1 second
            newly_duplicated.clear()
            duplicate_effect_timer = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEWHEEL:
            handle_scroll(mouse_pos, -event.y)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check for double click first
                is_double_click = double_click_handler.check_double_click(current_time, mouse_pos)
                
                if is_double_click:
                    # Handle double click - check if clicking on canvas element
                    double_clicked_element = None
                    for elem in reversed(canvas_elements):
                        if elem["rect"].collidepoint(mouse_pos):
                            double_clicked_element = elem
                            break
                    
                    if double_clicked_element:
                        # Duplicate the element
                        duplicate = duplicate_canvas_element(double_clicked_element, canvas_elements, SCREEN_WIDTH, SCREEN_HEIGHT)
                        newly_duplicated.append(duplicate)
                        duplicate_effect_timer = 0
                        print(f"Duplicated element: {duplicate['element']['name']}")
                        continue  # Skip normal click handling
                
                # Normal single click handling
                drag_sound.play()
                
                # Check mode button
                if mode_button_rect.collidepoint(mouse_pos):
                    is_light_mode = not is_light_mode
                
                # Check scrollbar
                scrollbar_thumb = get_scrollbar_thumb_rect()
                if scrollbar_thumb and scrollbar_thumb.collidepoint(mouse_pos):
                    scrolling = True
                    scroll_start_y = mouse_pos[1] - scrollbar_thumb.y
                
                # Check sidebar elements
                elif sidebar_rect.collidepoint(mouse_pos) and not scrolling:
                    for i, rect in element_rects:
                        if rect and rect.collidepoint(mouse_pos):
                            dragging_element = {
                                "element": elements[i],
                                "rect": pygame.Rect(mouse_pos[0], mouse_pos[1], rect.width, rect.height)
                            }
                            drag_offset = (mouse_pos[0] - rect.x, mouse_pos[1] - rect.y)
                            break

                # Check canvas elements
                if not dragging_element:
                    for elem in reversed(canvas_elements):
                        if elem["rect"].collidepoint(mouse_pos):
                            dragging_element = {
                                "element": elem["element"],
                                "rect": elem["rect"]
                            }
                            drag_offset = (mouse_pos[0] - elem["rect"].x, mouse_pos[1] - elem["rect"].y)
                            canvas_elements.remove(elem)
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                scrolling = False
                
                if dragging_element:
                    if sidebar_rect.collidepoint(mouse_pos):
                        dragging_element = None
                    else:
                        # Try combining
                        combined = False
                        for other in canvas_elements:
                            if other != dragging_element and other["rect"].colliderect(dragging_element["rect"]):
                                combine_sound.play()
                                name1 = dragging_element["element"]["name"]
                                name2 = other["element"]["name"]
                                combined_name = api_handler.call_gemini_api(name1, name2)
                                
                                if combined_name not in element_cache:
                                    elements.append({"name": combined_name})
                                    element_cache.add(combined_name)
                                    calculate_max_scroll()  # Recalculate scroll limits

                                new_rect = pygame.Rect(
                                    (dragging_element["rect"].x + other["rect"].x) // 2,
                                    (dragging_element["rect"].y + other["rect"].y) // 2,
                                    dragging_element["rect"].width,
                                    dragging_element["rect"].height
                                )
                                canvas_elements.append({
                                    "element": {"name": combined_name},
                                    "rect": new_rect
                                })

                                canvas_elements.remove(other)
                                combined = True
                                break

                        if not combined:
                            canvas_elements.append(dragging_element)
                    dragging_element = None

        elif event.type == pygame.MOUSEMOTION:
            if scrolling:
                # Handle scrollbar dragging
                scrollbar_thumb = get_scrollbar_thumb_rect()
                if scrollbar_thumb and max_scroll > 0:
                    new_thumb_y = mouse_pos[1] - scroll_start_y
                    relative_pos = (new_thumb_y - scrollbar_rect.y) / (scrollbar_rect.height - scrollbar_thumb.height)
                    scroll_offset = max(0, min(max_scroll, relative_pos * max_scroll))
            
            elif dragging_element:
                new_x = event.pos[0] - drag_offset[0]
                new_y = event.pos[1] - drag_offset[1]
                dragging_element["rect"].x = new_x
                dragging_element["rect"].y = new_y

    # Drawing
    draw_gradient_background(screen, BG_TOP, BG_BOTTOM)

    

    pygame.draw.rect(screen, WHITE, sidebar_rect, border_radius=25)
    # Draw title
    title_surface = title_font.render("Elements:", True, BLACK)
    screen.blit(title_surface, (sidebar_rect.x + 15, sidebar_rect.y + 20))

    # Create clipping rect for scrollable area
    clip_rect = pygame.Rect(sidebar_rect.x + 10, sidebar_rect.y + 60, 
                           sidebar_rect.width - 30, sidebar_rect.height - 70)
    screen.set_clip(clip_rect)

    # Draw elements
    element_rects = get_element_rects()
    for i, rect in element_rects:
        if rect:  # Only draw visible elements
            hover = rect.collidepoint(mouse_pos) and not scrolling
            bg_color = HOVER_COLOR if hover else LIGHT
            pygame.draw.rect(screen, bg_color, rect, border_radius=10)

            name = elements[i]["name"]
            label_surface = font.render(name, True, BLACK)
            label_rect = label_surface.get_rect(center=rect.center)
            screen.blit(label_surface, label_rect)

    # Remove clipping
    screen.set_clip(None)

    # Draw scrollbar if needed
    if max_scroll > 0:
        # Draw scrollbar track
        pygame.draw.rect(screen, LIGHT, scrollbar_rect, border_radius=7)
        
        # Draw scrollbar thumb
        thumb_rect = get_scrollbar_thumb_rect()
        if thumb_rect:
            thumb_color = SCROLLBAR_HOVER_COLOR if scrolling or thumb_rect.collidepoint(mouse_pos) else SCROLLBAR_COLOR
            pygame.draw.rect(screen, thumb_color, thumb_rect, border_radius=7)

    # Draw canvas elements with duplicate effect
    for elem in canvas_elements:
        is_new = elem in newly_duplicated
        draw_canvas_element_with_effect(screen, elem, font, is_new)

    # Draw dragging element
    if dragging_element:
        rect = dragging_element["rect"]
        pygame.draw.rect(screen, WHITE, rect, border_radius=12)
        label_surface = font.render(dragging_element['element']['name'], True, BLACK)
        label_rect = label_surface.get_rect(center=rect.center)
        screen.blit(label_surface, label_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()