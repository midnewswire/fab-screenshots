package com.fabapps.podcastflutter

import com.ryanheise.audioservice.AudioServiceActivity

/** AudioServiceActivity shares the Flutter engine with the background audio service, so episodes keep playing. */
class MainActivity : AudioServiceActivity()
