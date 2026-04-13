def set_comparison(x, y):
    set_x = set(x)
    set_y = set(y)

    total = set_x | set_y
    same = set_x.intersection(set_y)
    diff = total - same

    return dict(
        x=len(set_x),
        y=len(set_y),
        x_diff_y=len(set_x - set_y),
        y_diff_x=len(set_y - set_x),
        total=len(total),
        same=len(same),
        diff=len(diff)
    )
