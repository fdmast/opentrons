import pytest
from opentrons.trackers.pose_tracker import (
    absolute, init
)
from opentrons.instruments import Pipette
from opentrons.robot.gantry import Mover
from numpy import array, isclose


@pytest.fixture
def driver():
    class Driver:
        def move(self, target):
            pass

        def home(self, axis):
            pass

    return Driver()


def test_functional(driver):
    scale = array([
        [2, 0, 0, -1],
        [0, 2, 0, -2],
        [0, 0, 2, -3],
        [0, 0, 0,  1],
    ])

    back = array([
        [0.5,   0,   0, 0],
        [0,   0.5,   0, 0],
        [0,     0, 0.5, 0],
        [0,     0,   0, 1],
    ])

    left = Mover(driver=driver, axis_mapping={'z': 'Z'}, reference=id(scale))
    right = Mover(driver=driver, axis_mapping={'z': 'A'}, reference=id(scale))
    gantry = Mover(
        driver=driver,
        axis_mapping={'x': 'X', 'y': 'Y'},
        reference=id(scale),
    )

    state = init() \
        .add(id(scale), transform=scale) \
        .add(gantry, id(scale)) \
        .add(left, gantry) \
        .add(right, gantry) \
        .add('left', left, transform=back) \
        .add('right', right, transform=back)

    state = gantry.move(state, x=1, y=1)
    state = left.move(state, z=1)

    assert isclose(absolute(state, 'left'), (1, 1, 1)).all()
    assert isclose(absolute(state, 'right'), (1, 1, 1.5)).all()
    state = gantry.move(state, x=2, y=2)
    state = right.move(state, z=3)
    assert isclose(absolute(state, 'left'), (2, 2, 1)).all()
    assert isclose(absolute(state, 'right'), (2, 2, 3)).all()
    state = gantry.jog(state, axis='x', distance=1)
    assert isclose(absolute(state, 'left'), (3, 2, 1)).all()
    assert isclose(absolute(state, 'right'), (3, 2, 3)).all()
    state = right.jog(state, axis='z', distance=1)
    assert isclose(absolute(state, 'left'), (3, 2, 1)).all()
    assert isclose(absolute(state, 'right'), (3, 2, 4)).all()


def test_integration(robot):
    left = Pipette(robot, mount='left')
    robot.home()
    pose = left._move(robot.poses, 1, 1, 1)
    assert isclose(absolute(pose, left), (1, 1, 1)).all()
