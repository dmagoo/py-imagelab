"""Utilities to compare surfaces"""
import cv2
import pygame
import numpy as np


VERBOSE = False

MAX_RGB_SCORE = np.sqrt((255 * 255) * 3)


def get_match_percentage(score):
    return ((MAX_RGB_SCORE - score) / MAX_RGB_SCORE) * 100


def euclidean_score(source_array, candidate_array):
    """Euclidean distance in RGB color space, averaged per pixel."""
    diff = np.subtract(candidate_array.astype(int), source_array.astype(int))
    return np.average(np.sqrt(np.sum(np.multiply(diff, diff), axis=2)))


def lab_score(source_array, candidate_array):
    """Euclidean distance in CIELAB color space.
    Perceptually weighted — equal numerical distances correspond more closely
    to equal perceived color differences than RGB Euclidean does.
    """
    def to_lab(arr):
        # surfarray gives (width, height, 3); cv2 expects (height, width, 3)
        return cv2.cvtColor(
            np.ascontiguousarray(arr.astype(np.uint8).transpose(1, 0, 2)),
            cv2.COLOR_RGB2LAB
        ).astype(float)

    diff = to_lab(source_array) - to_lab(candidate_array)
    return np.average(np.sqrt(np.sum(diff * diff, axis=2)))


STRATEGIES = {
    "euclidean": euclidean_score,
    "lab": lab_score,
}


def match_score(source, candidate, clip_rect=None):
    """Convenience wrapper for euclidean scoring against full surfaces.
    Used for display stats and stopping conditions.
    """
    if clip_rect:
        source = source.subsurface(source.get_rect().clip(clip_rect)).copy()
        candidate = candidate.subsurface(candidate.get_rect().clip(clip_rect)).copy()
    source_array = pygame.surfarray.array3d(source)
    candidate_array = pygame.surfarray.array3d(candidate)
    return euclidean_score(source_array, candidate_array)


def best_match(source, contender, candidates, clip_rect=None, score_fn=None,
               candidates_are_clipped=False):
    """Return the candidate closest to source as [actions, surface, score].
    score_fn receives two numpy arrays (width, height, 3) uint8 and returns a float.
    If candidates_are_clipped is True, candidates are already clip-sized and
    the subsurface step is skipped for them.
    """
    if score_fn is None:
        score_fn = euclidean_score

    def to_array(surf):
        arr = pygame.surfarray.array3d(surf)
        if clip_rect:
            r = surf.get_rect().clip(clip_rect)
            return arr[r.left:r.right, r.top:r.bottom]
        return arr

    def candidate_to_array(surf):
        if candidates_are_clipped:
            return pygame.surfarray.array3d(surf)
        return to_array(surf)

    source_array = to_array(source)

    # Pre-process source once and bind into a single-argument scorer.
    # Avoids redundant source conversion (e.g. RGB->LAB) on every candidate.
    if score_fn is euclidean_score:
        source_int = source_array.astype(int)
        def _score(candidate_array):
            diff = np.subtract(candidate_array.astype(int), source_int)
            return np.average(np.sqrt(np.sum(np.multiply(diff, diff), axis=2)))
    elif score_fn is lab_score:
        source_lab = cv2.cvtColor(
            np.ascontiguousarray(source_array.astype(np.uint8).transpose(1, 0, 2)),
            cv2.COLOR_RGB2LAB
        ).astype(float)
        def _score(candidate_array):
            candidate_lab = cv2.cvtColor(
                np.ascontiguousarray(candidate_array.astype(np.uint8).transpose(1, 0, 2)),
                cv2.COLOR_RGB2LAB
            ).astype(float)
            diff = source_lab - candidate_lab
            return np.average(np.sqrt(np.sum(diff * diff, axis=2)))
    else:
        def _score(candidate_array):
            return score_fn(source_array, candidate_array)

    best = contender
    best_score = _score(to_array(contender))
    best_actions = []

    if best_score == 0:
        return [best_actions, best, best_score]

    for [candidate, actions] in candidates:
        score = _score(candidate_to_array(candidate))
        if score < best_score:
            best = candidate
            best_score = score
            best_actions = actions

    if VERBOSE:
        print("best score is %f" % best_score)

    return [best_actions, best, best_score]
