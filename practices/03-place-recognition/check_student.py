"""Проверка поведения функций на маленьком искусственном примере, не решение."""
import numpy as np
from student import find_top_k, recall_at_k

database = np.array([[0., 1.], [1., 0.], [-1., 0.]])
query = np.array([1., 0.])
before = database.copy()
assert list(find_top_k(query, database, 2)) == [1, 0], 'Проверьте направление сортировки'
assert list(find_top_k(query, database, 1)) == [1], 'Проверьте параметр k'
np.testing.assert_array_equal(database, before, err_msg='Не меняйте базу внутри функции')
predictions = np.array([[0, 1], [1, 0], [2, 0]])
positives = np.array([[True, False, False], [True, False, False], [False, True, False]])
assert np.isclose(recall_at_k(predictions, positives, 1), 1/3), 'Recall@1: ожидается 1/3'
assert np.isclose(recall_at_k(predictions, positives, 2), 2/3), 'Recall@2: ожидается 2/3'
print('Проверки пройдены. Теперь запускайте run_lab.py на ITLP-Campus.')
