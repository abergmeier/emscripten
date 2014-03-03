#ifndef __EMSCRIPTEN_COMMON_H__
#define __EMSCRIPTEN_COMMON_H__

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

typedef int EM_BOOL;
#define EM_FALSE 0
#define EM_TRUE  1
#define EM_NULL  (void*)0

typedef void (*emscripten_deleter)(void* instance, void* delete_args);

struct emscripten_type_base {
	uint32_t ref_count;
	emscripten_deleter deleter;
	void* delete_args;
};

void emscripten_type_base_init( emscripten_type_base* instance, emscripten_deleter deleter, void* delete_args );
void emscripten_type_base_ref( emscripten_type_base* instance );
emscripten_type_base* emscripten_type_base_unref( emscripten_type_base* instance ) __attribute__((warn_unused_result));

typedef int WindowProxy;

#ifdef __cplusplus
} // extern "C"
#endif

#endif //__EMSCRIPTEN_COMMON_H__

