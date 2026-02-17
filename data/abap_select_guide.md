# ABAP Open SQL SELECT Guide

In ABAP, use SELECT ... INTO TABLE for set-based retrieval.
Prefer explicit field lists instead of SELECT * for better performance and readability.
Use WHERE with indexed fields whenever possible.

Example:
SELECT carrid, connid, cityfrom, cityto
  FROM spfli
  INTO TABLE @DATA(lt_spfli)
  WHERE carrid = @lv_carrid.
