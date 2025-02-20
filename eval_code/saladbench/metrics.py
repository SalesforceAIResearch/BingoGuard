import numpy as np
from sklearn.metrics import (
    accuracy_score,
    auc,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    confusion_matrix,
)


def eval_auprc(targets, preds, print_=False):
    """Evaluate AUPRC.

    Args:
        targets (List[int]): Ground truth labels.
        preds (List[int]): Predicted labels.

    Returns:
        float: AUPRC.
    """
    precision, recall, thresholds = precision_recall_curve(targets, preds)
    auprc = auc(recall, precision)
    if print_:
        print(f"AUPRC: {np.round(auprc, 4)}")
    # TODO: do not round return values
    return auprc

def eval_macro_f1(targets, preds, print_=False):
    """Evaluate F1 score.

    Args:
        targets (List[int]): Ground truth labels.
        preds (List[int]): Predicted labels.

    Returns:
        Tuple[float, float, float, float]: Accuracy, Precision, Recall, F1 score.
    """
    f1 = f1_score(targets, preds, average='macro')
    if print_:
        print(f"F1: {np.round(f1, 4)}")
    # TODO: do not round return values
    # TODO: move print to outside
    # TODO: consider using a dict or namedtuple

def eval_f1(targets, preds, print_=False):
    """Evaluate F1 score.

    Args:
        targets (List[int]): Ground truth labels.
        preds (List[int]): Predicted labels.

    Returns:
        Tuple[float, float, float, float]: Accuracy, Precision, Recall, F1 score.
    """
    accuracy = accuracy_score(targets, preds)
    precision = precision_score(targets, preds)
    recall = recall_score(targets, preds)
    tn, fp, fn, tp = confusion_matrix(targets, preds).ravel()
    f1 = f1_score(targets, preds)
    fpr = fp/(fp + tn)
    if print_:
        print(f"Accuracy: {np.round(accuracy, 4)}")
        print(f"False Positive Rate: {np.round(fpr, 4)}")
        print(f"Precision: {np.round(precision, 4)}")
        print(f"Recall: {np.round(recall, 4)}")
        print(f"F1: {np.round(f1, 4)}")
    # TODO: do not round return values
    # TODO: move print to outside
    # TODO: consider using a dict or namedtuple
    return (accuracy, precision, fpr, recall, f1)

def eval_per_level_and_type_acc(targets, eval_labels, preds, messages, print_=False):
    """Evaluate F1 score.

    Args:
        targets (List[int]): Ground truth labels.
        preds (List[int]): Predicted labels.

    Returns:
        Tuple[float, float, float, float]: Accuracy, Precision, Recall, F1 score.
    """
    from collections import defaultdict, OrderedDict

    total_dict = OrderedDict()
    correct_dict = OrderedDict()
    levels = {'level1': [], 'level2': [], 'level3': [], 'level4': []}
    for label, eval_label, data, pred in zip(targets, eval_labels, messages, preds):
        level = data['level']
        category = data['category']
        lc_tuple = (level, category)
        if not lc_tuple in total_dict:
            total_dict[lc_tuple] = 1
            correct_dict[lc_tuple] = []
        else:
            total_dict[lc_tuple] += 1
        correct_dict[lc_tuple].append(pred)
        levels[level].append(pred)





    if print_:
        print(f"Level 1 accuracy: {sum(levels['level1']) / len(levels['level1'])}")
        print(f"Level 2 accuracy: {sum(levels['level2']) / len(levels['level2'])}")
        print(f"Level 3 accuracy: {sum(levels['level3']) / len(levels['level3'])}")
        print(f"Level 4 accuracy: {sum(levels['level4']) / len(levels['level4'])}")
        print(f"Level 1 std: {np.std(levels['level1'])}")
        print(f"Level 2 std: {np.std(levels['level2'])}")
        print(f"Level 3 std: {np.std(levels['level3'])}")
        print(f"Level 4 std: {np.std(levels['level4'])}")
        print(f"Level 1 max: {np.array(levels['level1'])}")
        print(f"Level 2 max: {np.array(levels['level2'])}")
        print(f"Level 3 max: {np.array(levels['level3'])}")
        print(f"Level 4 max: {np.array(levels['level4'])}")
