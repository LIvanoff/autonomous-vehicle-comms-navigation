"""Prepared RGB-D frame-to-frame odometry. No GT, neural network or pose reset.

PnP returns T_current_reference. We accumulate its inverse:
T_world_current = T_world_reference @ inv(T_current_reference).
World is the first camera optical frame (x right, y down, z forward).
"""
import cv2
import numpy as np


def backproject(uv, depth, K):
    uv = np.asarray(uv, np.float64)
    ij = np.rint(uv).astype(int)
    ok = ((ij[:, 0] >= 0) & (ij[:, 0] < depth.shape[1]) &
          (ij[:, 1] >= 0) & (ij[:, 1] < depth.shape[0]))
    z = np.zeros(len(uv))
    z[ok] = depth[ij[ok, 1], ij[ok, 0]]
    finite=np.isfinite(z)
    z[~finite]=0.
    ok &= finite & (z > .25) & (z < 6.)
    xyz = np.column_stack(((uv[:, 0]-K[0, 2])*z/K[0, 0],
                           (uv[:, 1]-K[1, 2])*z/K[1, 1], z))
    return xyz, ok


def estimate_pose(xyz, uv, K, config):
    if len(xyz) < 6:
        return None, np.empty(0, int), float('nan')
    ok, rv, tv, ii = cv2.solvePnPRansac(
        np.ascontiguousarray(xyz, np.float64), np.ascontiguousarray(uv, np.float64),
        K, None, iterationsCount=150, reprojectionError=config['ransac_pixels'],
        confidence=.999, flags=cv2.SOLVEPNP_EPNP)
    if not ok or ii is None or len(ii) < config['min_inliers']:
        return None, np.empty(0, int), float('nan')
    ii = ii.ravel()
    ok, rv, tv = cv2.solvePnP(xyz[ii], uv[ii], K, None, rv, tv, True,
                            flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return None, ii, float('nan')
    R = cv2.Rodrigues(rv)[0]
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = tv.ravel()
    px = cv2.projectPoints(xyz[ii], rv, tv, K, None)[0].reshape(-1, 2)
    error = float(np.sqrt(np.mean(np.sum((px-uv[ii])**2, axis=1))))
    return T, ii, error


class Odometry:
    def __init__(self, config):
        self.config = config
        cv2.setNumThreads(1)
        cv2.setRNGSeed(42)
        self.orb = cv2.ORB_create(nfeatures=int(config['max_features']), fastThreshold=12)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.ref = None
        self.T = np.eye(4)

    def process(self, rgb, depth, K):
        key, des = self.orb.detectAndCompute(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), None)
        uv = np.asarray([k.pt for k in key], np.float64).reshape(-1, 2)
        out = dict(T=self.T.copy(), status='lost', features=len(key), matches=0,
                   inliers=0, reprojection_rmse_px=None, uv=np.empty((0, 2)),
                   reference_uv=np.empty((0, 2)), inlier_mask=np.empty(0, bool))
        if des is None or len(key) < self.config['min_inliers']:
            out['reason']='too_few_features'; return out
        if self.ref is None:
            self.ref=(uv, des, depth.copy())
            out.update(status='initialized', reason='first_frame')
            return out
        ru, rd, rz = self.ref
        pairs = self.matcher.knnMatch(rd, des, k=2)
        matches = [m for row in pairs if len(row)==2 for m,n in [row]
                   if m.distance < self.config['ratio_test']*n.distance]
        # One observation per current feature, lowest distance first.
        unique={}
        for m in sorted(matches,key=lambda x:x.distance):
            unique.setdefault(m.trainIdx,m)
        matches=list(unique.values())
        a=np.asarray([ru[m.queryIdx] for m in matches]).reshape(-1,2)
        b=np.asarray([uv[m.trainIdx] for m in matches]).reshape(-1,2)
        xyz,valid=backproject(a,rz,K)
        xyz,a,b=xyz[valid],a[valid],b[valid]
        out.update(matches=len(xyz),uv=b,reference_uv=a)
        T,ii,error=estimate_pose(xyz,b,K,self.config)
        mask=np.zeros(len(xyz),bool);mask[ii]=True
        out.update(inlier_mask=mask,inliers=len(ii))
        if T is None:
            out['reason']='pnp_not_supported'; return out
        angle=np.degrees(np.linalg.norm(cv2.Rodrigues(T[:3,:3])[0]))
        if np.linalg.norm(T[:3,3])>self.config['max_step_m'] or angle>self.config['max_rotation_deg']:
            out['reason']='motion_gate';return out
        self.T=self.T@np.linalg.inv(T)
        self.ref=(uv,des,depth.copy())
        out.update(T=self.T.copy(),status='tracking',reason='ok',reprojection_rmse_px=error)
        return out
