#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

#define MAX_CHAR_CODE       255
#define PRINTF_BUF_SIZE     1024
#define SMALL_BUF_SIZE      256

#define check_buf(size, buf_size)                         \
    if ((size) >= buf_size - 2)                           \
        pdftex_fail("buffer overflow [%i bytes]", (int)(buf_size))

#define append_char_to_buf(c, p, buf, buf_size) do {       \
    if (c == 9)                                            \
        c = 32;                                            \
    if (c == 13 || c == EOF)                               \
        c = 10;                                            \
    if (c != ' ' || (p > buf && p[-1] != 32)) {            \
        check_buf(p - buf, buf_size);                      \
        *p++ = c;                                          \
    }                                                      \
} while (0)

#define append_eol(p, buf, buf_size) do {                  \
    if (p - buf > 1 && p[-1] != 10) {                      \
        check_buf(p - buf, buf_size);                      \
        *p++ = 10;                                         \
    }                                                      \
    if (p - buf > 2 && p[-2] == 32) {                      \
        p[-2] = 10;                                        \
        p--;                                               \
    }                                                      \
    *p = 0;                                                \
} while (0)

#define remove_eol(p, buf) do {                            \
    p = strend(buf) - 1;                                   \
    if (*p == 10)                                          \
        *p = 0;                                            \
} while (0)

#define skip(p, c)   if (*p == c)  p++
#define strend(s)           strchr(s, 0)
#define xtalloc(n, t) ((t *) xmalloc ((n) * sizeof (t)))
#define xfree(p)            do { if (p != 0) free(p); p = 0; } while (0)

#define false 0
#define true 1
#define xstrdup strdup
#define xmalloc malloc
#define xfclose(a, b) (fclose(a))
#define isdigit(c)  ((c) >= '0' && (c) <= '9')
#define search(a, b, c) (fopen(b, "r"))
#define integer int
#define boolean char
