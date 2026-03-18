
def get_course_values(row, tee):
    """Return slope and CR dynamically for any tee."""
    cr_col = f"CR {tee} Uomini"
    sr_col = f"Slope {tee} Uomini"

    cr = row.get(cr_col)
    sr = row.get(sr_col)

    return sr, cr
