#include <stdio.h>
#include <kpathsea/tex-file.h>

FILE* search(kpse_file_format_type format, char *file, char *mode)
{
  kpse_set_program_name("dvips", "dvips"); // this should be placed somewhere else; should be pretend to be dvips?
  // kpse_type1_format should be in parameter format, but it isn't -> fix the binding with writet1
  printf("%s\n", kpse_find_file(file, kpse_type1_format, 1));
  return fopen(kpse_find_file(file, kpse_type1_format, 1), mode);
}
