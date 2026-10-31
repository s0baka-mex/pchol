[app]
title = Худеем вместе
package.name = hudeemvmeste
package.domain = org.hudeem

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

requirements = python3,kivy,pyyaml,pillow

orientation = portrait

fullscreen = 0

android.api = 31
android.minapi = 21
android.ndk = r25b

p4a.source_dir = 

android.archs = arm64-v8a

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
