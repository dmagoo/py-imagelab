import pygame
import numpy as np

global VERBOSE


class ConvolutionFilter:
    """The abstract convolution filter"""
    c_matrix = None
    hotspot = None
    divisor = 1
    offset = 0

    def __init__(self, c_matrix=None, divisor=None, offset=None, hotspot=None):

        if c_matrix is not None:
            self.c_matrix = c_matrix

        if divisor is not None:
            self.divisor = divisor
        if offset is not None:
            self.offset = offset
        if hotspot is not None:
            self.hotspot = hotspot
        else:
            self.hotspot = (
                (len(self.c_matrix[0]) - 1)/2, (len(self.c_matrix)-1)/2
            )


class GaussianBlurFilter(ConvolutionFilter):
    """A simple gaussian blur filter"""
    c_matrix = [[1, 2, 1], [2, 4, 2], [1, 2, 1]]
    divisor = 16


class EmbossFilter(ConvolutionFilter):
    """A simple emboss filter"""
    c_matrix = [[-1, 0, -1], [0, 4, 0], [-1, 0, -1]]
    divisor = 1
    offset = 127


# These are filters that take a single surface and "do something" to it
#
def apply_filter(source_array, filter_array, divisor, offset=0, hotspot=None):
    """Takes a source array of pixel data and performs the convolution
       This is hardly called directly.  It is more often called via the 'filter
       surface' function
    """
    (filter_w, filter_h) = (len(filter_array[0]), len(filter_array))

    ret = np.zeros(source_array.shape)
    (surfW, surfH) = ret.shape[:2]

    if not divisor:
        divisor = 1

    if hotspot is None:
        hotspot = ((filter_w-1)/2, (filter_h-1)/2)

    # Define the clipping area that can be affected by the filter
    left_margin = hotspot[0]
    top_margin = hotspot[1]
    right_margin = filter_w - 1 - hotspot[0]
    bottom_margin = filter_h - 1 - hotspot[1]

    for f_vert_offset in range(0-hotspot[1], filter_h-hotspot[1]):
        for f_horiz_offset in range(0-hotspot[0], filter_w-hotspot[0]):
            if filter_array[f_vert_offset+1][f_horiz_offset+1] != 0:
                ret[
                    left_margin:surfW-right_margin,
                    top_margin:surfH-bottom_margin
                ] += source_array[
                    left_margin+f_horiz_offset:
                        surfW-right_margin+f_horiz_offset,
                    top_margin+f_vert_offset: surfH-bottom_margin+f_vert_offset
                ] * filter_array[f_vert_offset+1][f_horiz_offset+1]

    if divisor != 1:
        ret = np.divide(ret, divisor)
    if offset:
        ret = np.add(ret, offset)

    return np.clip(ret, 0, 255)


def filter_surface(surf, filterObj):
    """Takes a pygame surface and a convolution filter object,
       applies the filter to the surface in place
       """
    source_array = pygame.surfarray.array3d(surf).astype(int)

    ret = pygame.Surface((source_array.shape[0], source_array.shape[1]))
    pygame.surfarray.blit_array(ret, source_array)
    pygame.surfarray.blit_array(
        ret,
        apply_filter(
            source_array,
            filterObj.c_matrix,
            filterObj.divisor,
            filterObj.offset,
            filterObj.hotspot
        )
    )
    surf.blit(ret, (0, 0))


def apply_gaussian_blur(surf):
    f = GaussianBlurFilter()

    filter_surface(surf, f)


def apply_gaussian_blur2(surf):
    """ A more blurry version of the above... haven't automated dynamic matrix
        computation
        To implement look up gaussian
    """
    f = GaussianBlurFilter()
    f.c_matrix = [
                    [0, 1, 2, 1, 0], [1, 2, 4, 2, 1], [2, 4, 8, 4, 2],
                    [1, 2, 4, 2, 1], [0, 1, 2, 1, 0]
                ]
    f.divisor = 48
    filter_surface(surf, f)


def apply_emboss(surf):
    f = EmbossFilter()

    filter_surface(surf, f)


def mutate_pixels(source, morph_range=15, morph_chance=500):
    """
        Take a surface and change random pixes given the passed in probability
        and max rang
    """
    imgArray = np.array(pygame.surfarray.array3d(source))

    randArray = np.array(
        np.randint(-morph_range, morph_range+1, imgArray.shape)
    )
    randMask = np.array(np.randint(1, morph_chance, imgArray.shape))

    np.putmask(imgArray, randMask == 1, np.add(randArray, imgArray))

    img = pygame.Surface((imgArray.shape[0], imgArray.shape[1]))

    pygame.surfarray.blit_array(img, imgArray)

    return img


# These are filters that combine multiple surfaces in different ways
#
def average_surfaces(surface_list):
    """Take a bunch of surfaces and compute the pixel by pixel average"""
    s_sum = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_sum is None:
            s_sum = s_array
        else:
            s_sum = np.add(s_sum, s_array)

    s_sum = s_sum/len(surface_list)
    ret = pygame.Surface((s_sum.shape[0], s_sum.shape[1]))
    pygame.surfarray.blit_array(ret, s_sum)
    return ret


def average_subtract_outlier_surfaces(surface_list):
    """
        Take a bunch of surfaces and compute the pixel by pixel average,
        eliminate outliers
    """
    s_sum = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_sum is None:
            s_sum = s_array
        else:
            s_sum = np.add(s_sum, s_array)

    ret = pygame.Surface((s_sum.shape[0], s_sum.shape[1]))

    s_mask = None
    # Quick TODO: average w/ above code

    deviation_masks = []
    deviation_sum = None

    for s in surface_list:
        # create a mask of the largest deviant from the average
        s_array = pygame.surfarray.array3d(s).astype(int)

        deviation = np.abs(np.subtract(s_array, s_sum))
        deviation_masks.append(deviation)

        if deviation_sum is None:
            deviation_sum = deviation
        else:
            deviation_sum = np.add(deviation_sum, deviation)

    avg_deviation = deviation_sum/(len(deviation_masks))

    s_mask = None
    # Quick TODO: average w/ above code
    i = 0
    for s in surface_list:
        # create a mask of the largest deviant from the average
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_mask is None:
            s_mask = s_array
        else:
            np.putmask(s_mask, deviation_masks[i] > avg_deviation, s_array)
        i = i+1

    # todo, something w/ s_mask itself. It's puuurdy cool!
    s_sum = np.subtract(s_sum, s_mask)
    # we just canceled out an outlier.  So.. poof
    s_sum = s_sum/(len(surface_list)-1)
    pygame.surfarray.blit_array(ret, s_sum)
    return ret


def average_subtract_outlier_surfaces_a(surface_list):
    """
        Take a bunch of surfaces and compute the pixel by pixel average,
        eliminate outliers
    """
    s_sum = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_sum is None:
            s_sum = s_array
        else:
            s_sum = np.add(s_sum, s_array)

    ret = pygame.Surface((s_sum.shape[0], s_sum.shape[1]))

    s_mask = None
    # Quick TODO: average w/ above code
    for s in surface_list:
        # create a mask of the largest deviant from the average
        s_array = pygame.surfarray.array3d(s).astype(int)

    if s_mask is None:
        s_mask = s_array
    else:
        np.putmask(
            s_mask,
            np.abs(np.subtract(s_sum, s_array)) >
            np.abs(np.subtract(s_sum, s_mask)),
            s_array
        )

    # todo, something w/ s_mask itself. It's puuurdy cool!
    s_sum = np.subtract(s_sum, s_mask)
    # we just canceled out an outlier.  So.. poof
    s_sum = s_sum/(len(surface_list)-1)
    pygame.surfarray.blit_array(ret, s_sum)
    return ret


def difference_surfaces(surface_list):
    """Take a bunch of surfaces and compute the pixel by pixel difference"""
    s_diff = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_diff is None:
            s_diff = s_array
        else:
            s_diff = np.subtract(s_diff, s_array)

    s_diff = s_diff + 128 * (len(surface_list)-1)

    ret = pygame.Surface((s_diff.shape[0], s_diff.shape[1]))
    pygame.surfarray.blit_array(ret, s_diff)
    return ret


def absolute_difference(surface_list):
    s_diff = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_diff is None:
            s_diff = s_array
        else:
            s_diff = np.abs(np.subtract(s_diff, s_array))

    ret = pygame.Surface((s_diff.shape[0], s_diff.shape[1]))
    pygame.surfarray.blit_array(ret, s_diff)
    return ret


def darkest_surfaces(surface_list):
    s_diff = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_diff is None:
            s_diff = s_array
        else:
            np.putmask(s_diff, s_array < s_diff, s_array)

    ret = pygame.Surface((s_diff.shape[0], s_diff.shape[1]))
    pygame.surfarray.blit_array(ret, s_diff)
    return ret


def lightest_surfaces(surface_list):

    s_diff = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_diff is None:
            s_diff = s_array
        else:
            np.putmask(s_diff, s_array > s_diff, s_array)

    ret = pygame.Surface((s_diff.shape[0], s_diff.shape[1]))
    pygame.surfarray.blit_array(ret, s_diff)
    return ret


def multiply_surfaces(surface_list):
    s_diff = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_diff is None:
            s_diff = s_array
        else:
            s_diff = s_diff * s_array / 255

    ret = pygame.Surface((s_diff.shape[0], s_diff.shape[1]))
    pygame.surfarray.blit_array(ret, s_diff)

    return ret


def multiply_negative_surfaces(surface_list):
    s_diff = None

    for s in surface_list:
        s_array = pygame.surfarray.array3d(s).astype(int)

        if s_diff is None:
            s_diff = s_array
        else:
            s_diff = 255 - ((255-s_diff) * (255 - s_array) / 255)

    ret = pygame.Surface((s_diff.shape[0], s_diff.shape[1]))
    pygame.surfarray.blit_array(ret, s_diff)
    return ret
