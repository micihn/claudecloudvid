"""Make assets/wordmark.png: the PORTOKO wordmark as a white-on-transparent mask, cropped tight.
Source: ../teaser/assets/logo_mask.png (white letters on black, drawn from the brand logo)."""
import os, numpy as np, cv2
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = cv2.imread(os.path.join(HERE, '..', 'teaser', 'assets', 'logo_mask.png'), 0)
ys, xs = np.where(m > 8); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
out = np.dstack([np.full_like(m, 255)] * 3 + [m])
cv2.imwrite(os.path.join(HERE, 'assets', 'wordmark.png'), out)
print(out.shape)
