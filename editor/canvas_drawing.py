from PyQt5.QtCore import Qt, QPointF, QRect, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QImage, QLinearGradient
from collections import deque
import numpy as np

from .filters import to_array, from_array


class CanvasDrawingMixin:
    def draw_point(self, pos):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing)
        if self.has_selection():
            self._apply_selection_clip(p)
        c = self.tool_color
        c.setAlpha(int(255 * self.tool_opacity))
        pen = QPen(c, self.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawPoint(pos)
        p.end()
        self.layer_stack.invalidate_cache()
        self._refresh()

    def draw_line(self, p1, p2):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing)
        if self.has_selection():
            self._apply_selection_clip(p)
        c = self.tool_color
        c.setAlpha(int(255 * self.tool_opacity))
        pen = QPen(c, self.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawLine(p1, p2)
        p.end()
        self.layer_stack.invalidate_cache()
        self._refresh()

    def erase_point(self, pos):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing)
        if self.has_selection():
            self._apply_selection_clip(p)
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        pen = QPen(QColor(0, 0, 0, 0), self.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawPoint(pos)
        p.end()
        self.layer_stack.invalidate_cache()
        self._refresh()

    def erase_line(self, p1, p2):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing)
        if self.has_selection():
            self._apply_selection_clip(p)
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        pen = QPen(QColor(0, 0, 0, 0), self.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawLine(p1, p2)
        p.end()
        self.layer_stack.invalidate_cache()
        self._refresh()

    def _apply_pixel_op(self, pos, op_func, strength=1.0):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        radius = max(1, self.tool_size // 2)
        x, y = int(pos.x()), int(pos.y())
        w, h = layer.image.width(), layer.image.height()
        x0, y0 = max(0, x - radius), max(0, y - radius)
        x1, y1 = min(w, x + radius + 1), min(h, y + radius + 1)
        if x0 >= x1 or y0 >= y1:
            return
        rect = QRect(x0, y0, x1 - x0, y1 - y0)
        arr = to_array(layer.image.copy(rect)).astype(np.float32) / 255.0
        result = op_func(arr, strength)
        result = np.clip(result * 255.0, 0, 255).astype(np.uint8)
        new_img = from_array(result)
        p = QPainter(layer.image)
        p.setClipRect(rect)
        if self.has_selection():
            self._apply_selection_clip(p)
        p.drawImage(x0, y0, new_img)
        p.end()
        self.layer_stack.invalidate_cache()
        self._refresh()

    def _dodge_func(self, arr, exposure):
        result = np.clip(arr[..., :3] + (1.0 - arr[..., :3]) * exposure * 0.5, 0, 1)
        if arr.shape[2] == 4:
            result = np.concatenate([result, arr[..., 3:4]], axis=2)
        return result

    def _burn_func(self, arr, exposure):
        result = np.clip(arr[..., :3] - arr[..., :3] * exposure * 0.5, 0, 1)
        if arr.shape[2] == 4:
            result = np.concatenate([result, arr[..., 3:4]], axis=2)
        return result

    def _sponge_func(self, arr, amount):
        gray = np.mean(arr[..., :3], axis=2, keepdims=True)
        gray = np.repeat(gray, 3, axis=2)
        if amount > 0:
            result = arr[..., :3] + (arr[..., :3] - gray) * amount * 0.5
        else:
            result = arr[..., :3] + (gray - arr[..., :3]) * abs(amount) * 0.5
        result = np.clip(result, 0, 1)
        if arr.shape[2] == 4:
            result = np.concatenate([result, arr[..., 3:4]], axis=2)
        return result

    def dodge_point(self, pos, exposure=0.5):
        self._apply_pixel_op(pos, self._dodge_func, exposure)

    def burn_point(self, pos, exposure=0.5):
        self._apply_pixel_op(pos, self._burn_func, exposure)

    def saturate_point(self, pos, amount=0.5):
        self._apply_pixel_op(pos, self._sponge_func, amount)

    def dodge_line(self, p1, p2, exposure=0.5):
        steps = max(int(p1.distance(p2) / 2), 1)
        for t in range(steps + 1):
            frac = t / steps
            pt = QPointF(p1.x() + (p2.x() - p1.x()) * frac,
                         p1.y() + (p2.y() - p1.y()) * frac)
            self.dodge_point(pt, exposure)

    def burn_line(self, p1, p2, exposure=0.5):
        steps = max(int(p1.distance(p2) / 2), 1)
        for t in range(steps + 1):
            frac = t / steps
            pt = QPointF(p1.x() + (p2.x() - p1.x()) * frac,
                         p1.y() + (p2.y() - p1.y()) * frac)
            self.burn_point(pt, exposure)

    def saturate_line(self, p1, p2, amount=0.5):
        steps = max(int(p1.distance(p2) / 2), 1)
        for t in range(steps + 1):
            frac = t / steps
            pt = QPointF(p1.x() + (p2.x() - p1.x()) * frac,
                         p1.y() + (p2.y() - p1.y()) * frac)
            self.saturate_point(pt, amount)

    def get_pixel_color(self, pos):
        layer = self.layer_stack.active
        if not layer:
            return None
        x = max(0, min(int(pos.x()), layer.image.width() - 1))
        y = max(0, min(int(pos.y()), layer.image.height() - 1))
        return layer.image.pixelColor(x, y)

    def flood_fill(self, pos):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        x, y = int(pos.x()), int(pos.y())
        w_i, h_i = layer.image.width(), layer.image.height()
        if x < 0 or x >= w_i or y < 0 or y >= h_i:
            return

        target = layer.image.pixelColor(x, y)
        if target == self.tool_color:
            return

        q = deque()
        q.append((x, y))
        visited = {(x, y)}

        p = QPainter(layer.image)
        if self.has_selection():
            self._apply_selection_clip(p)
        p.setPen(QPen(self.tool_color, 1))

        while q:
            cx, cy = q.popleft()
            if layer.image.pixelColor(cx, cy) == target:
                p.drawPoint(cx, cy)
                for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
                    if 0 <= nx < w_i and 0 <= ny < h_i and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        q.append((nx, ny))
        p.end()
        self._refresh()

    def flood_fill_select(self, pos):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        x, y = int(pos.x()), int(pos.y())
        w_i, h_i = layer.image.width(), layer.image.height()
        if x < 0 or x >= w_i or y < 0 or y >= h_i:
            return

        target = layer.image.pixelColor(x, y)
        tolerance = 32

        q = deque()
        q.append((x, y))
        visited = np.zeros((h_i, w_i), dtype=bool)
        visited[y, x] = True

        mask = QImage(w_i, h_i, QImage.Format_ARGB32)
        mask.fill(Qt.transparent)

        while q:
            cx, cy = q.popleft()
            color = layer.image.pixelColor(cx, cy)
            diff = (abs(color.red() - target.red()) +
                    abs(color.green() - target.green()) +
                    abs(color.blue() - target.blue()))
            if diff <= tolerance:
                mask.setPixel(cx, cy, QColor(255, 255, 255).rgba())
                for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
                    if 0 <= nx < w_i and 0 <= ny < h_i and not visited[ny, nx]:
                        visited[ny, nx] = True
                        q.append((nx, ny))

        self.set_selection_mask_image(mask)

    def draw_gradient(self, start, end):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        w, h = layer.image.width(), layer.image.height()
        grad_obj = getattr(self, "gradient_obj", None)
        if grad_obj is not None and grad_obj.stops:
            grad = grad_obj.to_qgradient(start, end)
        else:
            grad = QLinearGradient(start, end)
            grad.setColorAt(0.0, self.tool_color)
            grad.setColorAt(1.0, self.bg_color)
        p = QPainter(layer.image)
        if self.has_selection():
            self._apply_selection_clip(p)
        p.fillRect(0, 0, w, h, grad)
        p.end()
        self._refresh()

    def draw_rect_shape(self, start, end):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing)
        if self.has_selection():
            self._apply_selection_clip(p)
        pen = QPen(self.tool_color, self.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        rect = QRectF(start, end)
        p.drawRect(rect.normalized())
        p.end()
        self._refresh()

    def draw_ellipse_shape(self, start, end):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing)
        if self.has_selection():
            self._apply_selection_clip(p)
        pen = QPen(self.tool_color, self.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        rect = QRectF(start, end)
        p.drawEllipse(rect.normalized())
        p.end()
        self._refresh()

    def clone_stamp(self, src, dst):
        layer = self.layer_stack.active
        if not layer or layer.locked:
            return
        sx, sy = int(src.x()), int(src.y())
        dx, dy = int(dst.x()), int(dst.y())
        w, h = layer.image.width(), layer.image.height()
        if not (0 <= sx < w and 0 <= sy < h and 0 <= dx < w and 0 <= dy < h):
            return
        color = layer.image.pixelColor(sx, sy)
        p = QPainter(layer.image)
        if self.has_selection():
            self._apply_selection_clip(p)
        pen = QPen(color, self.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawPoint(dx, dy)
        p.end()
        self._refresh()
