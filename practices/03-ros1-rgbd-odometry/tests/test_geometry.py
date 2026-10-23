"""Independent synthetic projection: checks transform direction, outliers and missing data."""
import unittest
import cv2
import numpy as np
from rgbd_vo_lab.geometry import backproject,estimate_pose,Odometry

C=dict(max_features=1000,min_inliers=20,ratio_test=.75,ransac_pixels=2.5,max_step_m=.3,max_rotation_deg=25.)

class GeometryTests(unittest.TestCase):
    def test_motion_and_outliers(self):
        rng=np.random.RandomState(42);xyz=rng.uniform([-1,-.7,2],[1,.7,4],(120,3))
        K=np.array([[525.,0,319.5],[0,525.,239.5],[0,0,1.]])
        rv=np.array([.01,-.025,.02]);tv=np.array([-.08,.01,.015])
        uv=cv2.projectPoints(xyz,rv,tv,K,None)[0].reshape(-1,2)
        uv[:25]=rng.uniform([0,0],[640,480],(25,2))
        T,ii,err=estimate_pose(xyz,uv,K,C)
        self.assertGreater(len(ii),85)
        np.testing.assert_allclose(T[:3,3],tv,atol=1e-5)
        np.testing.assert_allclose(T[:3,:3],cv2.Rodrigues(rv)[0],atol=1e-5)
        # Camera center in previous/world frame must be -R^T t, not t.
        np.testing.assert_allclose(np.linalg.inv(T)[:3,3],-T[:3,:3].T@tv,atol=1e-5)

    def test_invalid_depth(self):
        z=np.array([[0,np.nan],[2,np.inf]],np.float32)
        xyz,ok=backproject([[0,0],[1,0],[0,1],[1,1],[-1,0]],z,np.eye(3))
        self.assertEqual(ok.tolist(),[False,False,True,False,False])
        np.testing.assert_allclose(xyz[2],[0,2,2])

    def test_blank_frame_is_not_motion(self):
        engine=Odometry(C)
        r=engine.process(np.zeros((480,640,3),np.uint8),np.ones((480,640),np.float32),np.eye(3))
        self.assertEqual(r['status'],'lost');self.assertIsNone(engine.ref)
        np.testing.assert_array_equal(r['T'],np.eye(4))

if __name__=='__main__':unittest.main()
