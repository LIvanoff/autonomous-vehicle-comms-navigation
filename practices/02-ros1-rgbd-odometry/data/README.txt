Бэг скачивается отдельно (около 75 МБ):
https://github.com/LIvanoff/autonomous-vehicle-comms-navigation/raw/29c96ba7e98efba7c77fafe587646913174e33c1/practices/02-ros1-rgbd-odometry/data/tum_rgbd_12s.bag
Сохраните файл в эту папку под именем tum_rgbd_12s.bag.

Учебный bag: tum_rgbd_12s.bag
Источник: TUM RGB-D Dataset, freiburg1_xyz.
J. Sturm, N. Engelhard, F. Endres, W. Burgard, D. Cremers.
A Benchmark for the Evaluation of RGB-D SLAM Systems, IROS 2012.
https://cvg.cit.tum.de/data/datasets/rgbd-dataset

Лицензия датасета: Creative Commons Attribution 4.0 (CC BY 4.0).
https://creativecommons.org/licenses/by/4.0/
Атрибуция и ссылка на исходный датасет приведены выше.
Изменения: выбран фрагмент около 12 с, частота уменьшена примерно до 10 Гц,
RGB/depth сопоставлены по ближайшей метке <=20 мс, depth переведена в метры.
Метка RGB скопирована к сопоставленной depth для TimeSynchronizer.
Исходная метка глубины сохранена в tum_rgbd_12s.json.
Поза эталона интерполирована (позиция линейно, ориентация SLERP).
В бэге K=ROS default согласно рекомендации TUM для pre-registered depth.
Дополнительная коррекция масштаба depth не применялась: она уже сделана TUM.

Скачать исходный архив и пересобрать (преподавателю):
https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz
В контейнере с ROS:
  python3 tools/prepare_tum.py data/rgbd_dataset_freiburg1_xyz.tgz --out data/rebuilt.bag
Скрипт не перезаписывает существующий bag.
