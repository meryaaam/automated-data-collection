import skimage.filters as filters
import cv2

for i in range(1,49):
    s = '![image](./jiangyi3/img'+str(i)+'.jpg)'
    print(s)


def remove_img_watermark() : 



    image = cv2.imread('ingrained.jpeg')

    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    smooth1 = cv2.GaussianBlur(gray, (5,5), 0)
    division1 = cv2.divide(gray, smooth1, scale=255)

    sharpened = filters.unsharp_mask(division1, radius=3, amount=7, preserve_range=False)
    sharpened = (255*sharpened).clip(0,255).astype(np.uint8)

    # line segments
    components, output, stats, centroids = cv2.connectedComponentsWithStats(sharpened, connectivity=8)
    sizes = stats[1:, -1]; components = components - 1
    size = 100
    result = np.zeros((output.shape))
    for i in range(0, components):
        if sizes[i] >= size:
            result[output == i + 1] = 255

    cv2.imwrite('image-after.jpeg',result)