"""Create a real Rerun recording and optionally host the web viewer. No X11."""
import argparse,json,time
from pathlib import Path
import numpy as np
from PIL import Image
import rerun as rr
import rerun.blueprint as rrb


def main():
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path)
    p.add_argument('--serve',action='store_true');p.add_argument('--web-port',type=int,default=9090)
    p.add_argument('--grpc-port',type=int,default=9876);a=p.parse_args()
    rr.init('RGB-D visual odometry lab v2')
    rr.save(str(a.folder/'recording.rrd'))
    if a.serve:
        rr.serve_grpc(grpc_port=a.grpc_port,server_memory_limit='256MiB')
        rr.serve_web_viewer(web_port=a.web_port,open_browser=False)
    input_report=a.folder/'input_report.json'
    if input_report.exists():
        data=json.loads(input_report.read_text())
        rr.log('description',rr.TextDocument('nuPlan: RGB only, 2 Hz.\nNo measured depth or camera calibration in this bag.\nThis view shows INPUT frames, not estimated motion or a 3D reconstruction.'),static=True)
        for i,item in enumerate(data['frames']):
            rr.set_time('frame',sequence=i)
            rr.log('rgb',rr.Image(np.asarray(Image.open(a.folder/item['file']).resize((960,540)))).compress(jpeg_quality=85))
        rr.send_blueprint(rrb.Blueprint(rrb.Horizontal(rrb.Spatial2DView(origin='rgb',name='nuPlan RGB input'),
                                                     rrb.TextDocumentView(origin='description',name='Input limitations'))))
    else:
        report=json.loads((a.folder/'report.json').read_text())
        gt=np.load(a.folder/'ground_truth.npz')['T']
        rr.log('world',rr.ViewCoordinates.RDF,static=True)
        rr.log('trajectory',rr.ViewCoordinates.RDF,static=True)
        rr.log('world/reference',rr.LineStrips3D([gt[:,:3,3]],colors=[65,195,125],radii=.003),static=True)
        rr.log('trajectory/reference',rr.LineStrips3D([gt[:,:3,3]],colors=[65,195,125],radii=.002),static=True)
        rr.log('path_xz/reference',rr.LineStrips2D([gt[:,[0,2],3]],colors=[65,195,125],radii=.002),static=True)
        rr.log('description',rr.TextDocument('Orange: RGB-D estimated path. Green: motion capture reference.\n'+
               'World = first camera optical frame (x right, y down, z forward).\n'+
               'Reference aligned ONLY by first pose; no scale fitting.\n'+
               json.dumps(report,indent=2)),static=True)
        path=[]
        for f in sorted((a.folder/'frames').glob('*.npz')):
            with np.load(f) as d:
                index=int(d['index']);rr.set_time('frame',sequence=index)
                rgb=d['rgb'];z=d['depth'];K=d['K'];T=d['T'];status=str(d['status'])
                rr.log('rgb',rr.Image(rgb).compress(jpeg_quality=85))
                rr.log('depth',rr.DepthImage(z,meter=1.))
                uv=d['uv'];prev=d['reference_uv'];mask=d['inlier_mask']
                if len(mask)==len(uv):
                    colors=np.where(mask[:,None],np.array([[65,240,140]]),np.array([[255,80,80]]))
                    rr.log('rgb/matches',rr.LineStrips2D(np.stack((prev,uv),axis=1),colors=colors))
                else:rr.log('rgb/matches',rr.Clear(recursive=True))
                rr.log('status',rr.TextDocument(f'Frame {index}: {status}\nFeatures: {int(d["features"])}\nMatches with depth: {int(d["matches"])}\nInliers: {int(d["inliers"])}\nReason: {str(d["reason"])}'))
                if status!='lost':
                    path.append(T[:3,3].copy())
                    rr.log('world/estimate',rr.LineStrips3D([np.asarray(path)],colors=[255,170,45],radii=.004))
                    rr.log('trajectory/estimate',rr.LineStrips3D([np.asarray(path)],colors=[255,170,45],radii=.002))
                    rr.log('path_xz/estimate',rr.LineStrips2D([np.asarray(path)[:,[0,2]]],colors=[255,170,45],radii=.002))
                    rr.log('world/camera',rr.Transform3D(translation=T[:3,3],mat3x3=T[:3,:3]))
                    rr.log('world/camera/image',rr.Pinhole(image_from_camera=K,resolution=[rgb.shape[1],rgb.shape[0]],image_plane_distance=.10))
                    rr.log('world/camera/image',rr.Image(rgb).compress(jpeg_quality=75))
                    # Sparse preview map only: actual pose estimation uses full RGB-D.
                    if len(path)%5==1:
                        yy,xx=np.mgrid[0:z.shape[0]:8,0:z.shape[1]:8];zz=z[::8,::8]
                        valid=np.isfinite(zz)&(zz>.25)&(zz<4.)
                        xyz=np.stack(((xx-K[0,2])*zz/K[0,0],(yy-K[1,2])*zz/K[1,1],zz),axis=-1)[valid]
                        world=xyz@T[:3,:3].T+T[:3,3]
                        rr.log('world/map/frame_%05d'%index,rr.Points3D(world,colors=rgb[::8,::8][valid],radii=.003))
        projected=np.concatenate((gt[:,[0,2],3],np.asarray(path)[:,[0,2]]))
        lo=projected.min(axis=0);hi=projected.max(axis=0);margin=np.maximum((hi-lo)*.15,.05)
        bounds=rrb.VisualBounds2D(x_range=[lo[0]-margin[0],hi[0]+margin[0]],y_range=[lo[1]-margin[1],hi[1]+margin[1]])
        rr.send_blueprint(rrb.Blueprint(rrb.Horizontal(
            rrb.Tabs(rrb.Spatial2DView(origin='path_xz',name='Траектории: плоскость XZ, м',visual_bounds=bounds),
                     rrb.Spatial3DView(origin='trajectory',name='Траектории 3D'),
                     rrb.Spatial3DView(origin='world',name='Карта RGB-D'),
                     rrb.TextDocumentView(origin='description',name='Проверка'),active_tab=0),
            rrb.Vertical(rrb.Spatial2DView(origin='rgb',name='Соответствия на кадрах'),
                         rrb.Spatial2DView(origin='depth',name='Измеренная глубина, м'),
                         rrb.TextDocumentView(origin='status',name='Отслеживание'),row_shares=[4,4,2])),
            collapse_panels=True))
    rr.get_global_data_recording().flush(blocking=True)
    print('Saved:',a.folder/'recording.rrd',flush=True)
    if a.serve:
        print(f'http://localhost:{a.web_port}/?url=rerun%2Bhttp%3A%2F%2Flocalhost%3A{a.grpc_port}%2Fproxy',flush=True)
        try:
            while True:time.sleep(1)
        except KeyboardInterrupt:pass


if __name__=='__main__':main()
