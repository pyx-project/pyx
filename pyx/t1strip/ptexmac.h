#ifndef PDFTEXMAC
#define PDFTEXMAC

/* Pascal WEB macros */
#define maxinteger 0x7FFFFFFF
#define maxdimen   0x3FFFFFFF

#define objinfo(n) objtab[n].int0

#define pdfroom(n) do {                                 \
    if (pdfbufsize - n < 0)                             \
        pdftex_fail("PDF output buffer overflowed");    \
    if (pdfptr + n >= pdfbufsize)                       \
        pdfflush();                                     \
} while (0)

#define pdfout(c)  do {             \
    if (pdfptr + 1 >= pdfbufsize)   \
        pdfflush();                 \
    pdfbuf[pdfptr++] = c;           \
} while (0)

#define pdfoffset()     (pdfgone + pdfptr)
#define pdfinitfont(f)  {tmpf = f; pdfcreatefontobj();}

#define pdfmovechars        getintpar(cfgmovecharscode)

/* pdftexlib macros */
#if defined(WIN32) || defined(__MINGW32__)
#define M_PI       3.1415926535897932385E0  /*Hex  2^ 1 * 1.921FB54442D18 */
#define M_PI_2     1.5707963267948966192E0  /*Hex  2^ 0 * 1.921FB54442D18 */
#define M_PI_4     7.8539816339744830962E-1 /*Hex  2^-1 * 1.921FB54442D18 */
#endif

#define MAX_CHAR_CODE       255
#define MOVE_CHARS_OFFSET   160

#define FF_BUF_SIZE         0x1000
#define PRINTF_BUF_SIZE     1024
#define MAX_CSTRING_LEN     1024

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

#define entry_room(t, n, s) do {                            \
    if (t##_tab == 0) {                                     \
        t##_max = (s);                                      \
        t##_tab = xtalloc(t##_max, t##_entry);              \
        t##_ptr = t##_tab;                                  \
    }                                                       \
    else if (t##_ptr - t##_tab + n >= t##_max) {            \
        last_tab_index = t##_ptr - t##_tab;                 \
        t##_tab = xretalloc(t##_tab, t##_max + (s), t##_entry); \
        t##_ptr = t##_tab + last_tab_index;                 \
        t##_max += (s);                                     \
    }                                                       \
} while (0)

#define xfree(p)            do { if (p != 0) free(p); p = 0; } while (0)
#define strend(s)           strchr(s, 0)
#define xtalloc             XTALLOC
#define xretalloc           XRETALLOC

#define ASCENT_CODE         0
#define CAPHEIGHT_CODE      1
#define DESCENT_CODE        2
#define FONTNAME_CODE       3
#define ITALIC_ANGLE_CODE   4
#define STEMV_CODE          5
#define XHEIGHT_CODE        6
#define FONTBBOX1_CODE      7
#define FONTBBOX2_CODE      8
#define FONTBBOX3_CODE      9
#define FONTBBOX4_CODE      10
#define MAX_KEY_CODE        (FONTBBOX1_CODE + 1)
#define FONT_KEYS_NUM       (FONTBBOX4_CODE + 1)

#define F_INCLUDED          0x01
#define F_SUBSETTED         0x02
#define F_TRUETYPE          0x04
#define F_BASEFONT          0x08
#define F_NOPARSING         0x10
#define F_PGCFONT           0x20

#define set_included(fm)    ((fm)->type |= F_INCLUDED)
#define set_subsetted(fm)   ((fm)->type |= F_SUBSETTED)
#define set_truetype(fm)    ((fm)->type |= F_TRUETYPE)
#define set_basefont(fm)    ((fm)->type |= F_BASEFONT)
#define set_noparsing(fm)   ((fm)->type |= F_NOPARSING)
#define set_pcgfont(fm)     ((fm)->type |= F_PGCFONT)

#define unset_included(fm)  ((fm)->type &= ~F_INCLUDED)
#define unset_subsetted(fm) ((fm)->type &= ~F_SUBSETTED)
#define unset_truetype(fm)  ((fm)->type &= ~F_TRUETYPE)
#define unset_basefont(fm)  ((fm)->type &= ~F_BASEFONT)
#define unset_noparsing(fm) ((fm)->type &= ~F_NOPARSING)
#define unset_pcgfont(fm)   ((fm)->type &= ~F_PGCFONT)

#define is_included(fm)     ((fm)->type & F_INCLUDED)
#define is_subsetted(fm)    ((fm)->type & F_SUBSETTED)
#define is_truetype(fm)     ((fm)->type & F_TRUETYPE)
#define is_basefont(fm)     ((fm)->type & F_BASEFONT)
#define is_noparsing(fm)    ((fm)->type & F_NOPARSING)

#define fm_slant(fm)        (fm)->slant
#define fm_extend(fm)       (fm)->extend
#define fm_fontfile(fm)     (fm)->ff_name

#define is_reencoded(fm)    ((fm)->encoding >= 0)
#define is_t1fontfile(fm)   (fm_fontfile(fm) != 0 && !is_truetype(fm))
#define is_pcgfont(fm)      (fm_fontfile(fm) == 0 && !is_basefont(fm))
#define need_encoding_obj(fm) (is_reencoded(fm) || is_subsetted(fm))

#define unset_fontfile(fm)  xfree((fm)->ff_name)

#define set_cur_file_name(s)      \
    cur_file_name = s;      \
    packfilename(maketexstring(cur_file_name), getnullstr(), getnullstr())

#define INDEXED_GLYPH_PREFIX    "index"

#define SMALL_BUF_SIZE      256

#endif  /* PDFTEXMAC */
