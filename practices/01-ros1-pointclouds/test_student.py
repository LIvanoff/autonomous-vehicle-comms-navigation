"""Tests for the provided geometry; these do not test the student's ROS TODOs.

Run at any time: python3 -m unittest test_student -v.
"""
import unittest
import numpy as np
from student_node import rotation_matrix, correct_points


class GeometryTests(unittest.TestCase):
    def test_identity(self):
        np.testing.assert_allclose(rotation_matrix(0,0,0),np.eye(3),atol=1e-12)
    def test_right_handed_quarter_turn(self):
        r=rotation_matrix(0,0,90)
        np.testing.assert_allclose(correct_points(np.array([[1.,0,0]]),r),[[0,1,0]],atol=1e-12)
    def test_order_xyz(self):
        r=rotation_matrix(90,90,0)
        np.testing.assert_allclose(correct_points(np.array([[0.,1,0]]),r),[[1,0,0]],atol=1e-12)
    def test_rotation_not_reflection(self):
        r=rotation_matrix(37,-21,14)
        np.testing.assert_allclose(r.T@r,np.eye(3),atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(r),1.)
    def test_invalid_and_input_unchanged(self):
        a=np.array([[1.,2,3],[np.nan,2,3],[1,np.inf,4]])
        original=a.copy(); result=correct_points(a,rotation_matrix(17,42,-81))
        np.testing.assert_equal(a,original); np.testing.assert_equal(result[1:],a[1:])
        self.assertEqual(result.shape,a.shape)
    def test_inverse_and_distances(self):
        a=np.array([[2.,-3,4],[-1.,5,8],[0.,0,0]])
        r=rotation_matrix(143,22,-71); b=correct_points(a,r)
        np.testing.assert_allclose(correct_points(b,r.T),a,atol=1e-12)
        self.assertAlmostEqual(np.linalg.norm(b[0]-b[1]),np.linalg.norm(a[0]-a[1]))


if __name__=='__main__': unittest.main()
