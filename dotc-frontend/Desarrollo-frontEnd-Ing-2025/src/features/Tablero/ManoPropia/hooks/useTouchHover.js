import { useRef, useState } from 'react';

export function useTouchHover({ isDisabled, longPressMs = 250, onSelectIndex } = {}) {
  const containerRef = useRef(null);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [isTouchHover, setIsTouchHover] = useState(false);
  const touchIdRef = useRef(null);
  const startPosRef = useRef({ x: 0, y: 0 });
  const timerRef = useRef(null);

  const getIndexFromPoint = (x, y) => {
    const el = containerRef.current;
    if (!el) return null;
    const cards = Array.from(el.getElementsByClassName('carta-visual'));
    if (!cards.length) return null;

    // Top-most bajo el dedo (respeta z-index y transforms)
    const stack = document.elementsFromPoint(x, y);
    const topCardEl = stack
      .filter((node) => node instanceof Element)
      .map((node) => node.closest?.('.carta-visual'))
      .find((cardEl) => cardEl && el.contains(cardEl));

    if (topCardEl) {
      const idx = cards.indexOf(topCardEl);
      if (idx !== -1) return idx;
    }

    // Fallback por distancia al centro
    let bestIdx = 0;
    let bestDist = Infinity;
    for (let i = 0; i < cards.length; i++) {
      const rect = cards[i].getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = x - cx;
      const dy = y - cy;
      const d = dx * dx + dy * dy;
      if (d < bestDist) {
        bestDist = d;
        bestIdx = i;
      }
    }
    return bestIdx;
  };

  const clearPress = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    touchIdRef.current = null;
  };

  const onTouchStart = (e) => {
    if (isDisabled) return;
    if (e.touches.length !== 1) return;
    const t = e.touches[0];
    touchIdRef.current = t.identifier;
    startPosRef.current = { x: t.clientX, y: t.clientY };

    timerRef.current = setTimeout(() => {
      setIsTouchHover(true);
      const idx = getIndexFromPoint(startPosRef.current.x, startPosRef.current.y);
      setHoveredIndex(idx);
    }, longPressMs);
  };

  const onTouchMove = (e) => {
    const id = touchIdRef.current;
    if (id == null) return;
    const t = Array.from(e.touches).find((tt) => tt.identifier === id);
    if (!t) return;

    if (!isTouchHover) return;

    // En hover táctil: evitar scroll y actualizar índice
    e.preventDefault();
    const idx = getIndexFromPoint(t.clientX, t.clientY);
    setHoveredIndex(idx);
  };

  const onTouchEndOrCancel = () => {
    if (!isDisabled && isTouchHover && hoveredIndex != null) {
      onSelectIndex?.(hoveredIndex);
    }
    setIsTouchHover(false);
    setHoveredIndex(null);
    clearPress();
  };

  const bind = {
    onTouchStart,
    onTouchMove,
    onTouchEnd: onTouchEndOrCancel,
    onTouchCancel: onTouchEndOrCancel,
  };

  return { containerRef, hoveredIndex, setHoveredIndex, isTouchHover, bind };
}