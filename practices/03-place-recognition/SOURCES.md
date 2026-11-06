# Источники и изменения

## ITLP-Campus Outdoor

- Авторы/проект: OPR-Project / ITLP-Campus; Александр Мелехин, Дмитрий Юдин и команда проекта.
- [Репозиторий и описание](https://github.com/OPR-Project/ITLP-Campus).
- [Оригинальные данные](https://huggingface.co/datasets/OPR-Project/ITLP-Campus-Outdoor).
- Лицензия данных: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), согласно README проекта.
- Изменения: взята только передняя камера; кадры уменьшены до 640×360, перекодированы в JPEG с quality=90; выбрана небольшая детерминированная подвыборка. Координаты XY взяты из `track.csv` без изменений.
- База: каждый второй кадр `07_2023-10-04-day`; запросы: 30 равномерно распределённых по индексу кадров из каждого проезда `05_2023-08-15-day` и `08_2023-10-11-night`.
- Полные URL источников каждого кадра, номера строк, координаты и SHA-256 производных изображений находятся в `data/manifest.json`. Скрипт `prepare_data.py` воспроизводит подготовку из оригиналов, но для занятия повторная загрузка не нужна.
- Дневные запросы относятся к другому сезону: сравнение «день/ночь» здесь не является экспериментом, где изменилось только освещение.

## OPR: модель и веса

- [OpenPlaceRecognition](https://github.com/OPR-Project/OpenPlaceRecognition), commit `ded86f5e7b998e94d9adb5eee5cc38528995dba6`.
- `third_party/opr_resnet.py` — файл `src/opr/modules/feature_extractors/resnet.py` из этого commit без изменений. Лицензия Apache-2.0 сохранена в `third_party/OPR_LICENSE`.
- Backbone из OPR использует код MinkLocMultimodal (MIT); его лицензия сохранена в `third_party/MinkLocMultimodal_LICENSE`.
- `model.py` — небольшой учебный адаптер единственной модели ResNet18 + GeM: backbone OPR, эквивалентный GeM и обработка одного изображения. Полный пакет OPR, его мультимодальные модели и pipeline не устанавливаются. Адаптер нужен, чтобы не тянуть обучение, CUDA, TensorRT и зависимости для лидаров.
- Архитектура: первые четыре уровня OPR ResNet18FPN, `num_top_down=0`, 256 каналов и GeM. Это именно вариант OPR, а не обычный полный классификатор torchvision ResNet18.
- [Веса `resnet18-gem_nclt.pth`](https://huggingface.co/OPR-Project/PlaceRecognition-NCLT/blob/main/resnet18-gem_nclt.pth), Apache-2.0. Карточка модели сохранена в `third_party/WEIGHTS_MODEL_CARD.md`.
- Веса обучены авторами на [NCLT](https://robots.engin.umich.edu/nclt/), исходный датасет NCLT — ODbL. Авторы NCLT не подтверждают результаты нашей практики. Веса не дообучались на данной учебной выборке ITLP.
- Контрольная сумма весов: `235c0f6a2f98bcb903c8646bb1317452a49e68ad690675172560a511d54f14c1`.
- Предобработка: RGB, 320×192, bilinear PIL; нормирование ImageNet; выходной дескриптор нормируется по L2. Это явно зафиксированная учебная предобработка, не заявка на воспроизведение официального benchmark OPR.

Кэш дескрипторов производный от указанных данных и модели; идентификаторы изображений и контрольные суммы привязаны к нему. Результаты и изображения необходимо распространять с этой атрибуцией.
