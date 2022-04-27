""" Utilities to compare surfaces """
import pygame
import numpy as np


VERBOSE = False

MAX_RGB_SCORE = np.sqrt((255*255)*3)


def get_match_percentage(match_score):
    return ((MAX_RGB_SCORE - match_score)/MAX_RGB_SCORE) * 100


def match_score(source, candidate, clip_rect=None):
    """Take two surfaces and compute their similarity.
       If clip_rect is given, only do so within the bounding area"""
    if clip_rect:
        source_array = pygame.surfarray.array3d(source.subsurface(
            source.get_rect().clip(clip_rect)).copy()).astype(int)
        candidate_array = pygame.surfarray.array3d(candidate.subsurface(
            candidate.get_rect().clip(clip_rect)).copy()).astype(int)
    else:
        source_array = pygame.surfarray.array3d(source).astype(int)
        candidate_array = pygame.surfarray.array3d(candidate).astype(int)

    # subtract each rgb value
    test = np.subtract(candidate_array, source_array)*1

    # sum r + g + b and take the sqrt,
    # the '2' says to sum along the third dimension
    # might be better to use the YUV color space or something
    # more suitable for visual perception
    test = np.sqrt(np.sum(np.multiply(test, test), 2))

    score = np.average(np.average(test))

    return score


def best_match(source, contender, list, clip_rect=None):
    """take a list of surfaces and a target, return the closest match
       which is defined as [action, surface, score]
    """
    best = contender
    best_score = match_score(source, contender, clip_rect)
    best_actions = []
    if best_score == 0:
        return [best_actions, best, best_score]

    for [candidate, actions] in list:
        score = match_score(source, candidate, clip_rect)

        # best score is smaller because it's how big the difference is
        if score < best_score:
            best = candidate
            best_score = score
            best_actions = actions

    if VERBOSE:
        print('best score is %f' % best_score)

    return [best_actions, best, best_score]
