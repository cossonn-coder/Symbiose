(function (K) {
  K.skyEnvironment = SkyEnvironment;
  K.environmentFrame = EnvironmentFrame;
  K.horizonBands = HorizonBands;
  K.artDirection = ArtDirection;
  K.celestialTracks = CelestialTracks;
  K.clouds = CloudField;
  K.reflection = {
    plane: SceneOptics.plane,
    reflectedView: SceneOptics.reflectedView,
    captureView: SceneOptics.captureView,
    material(base, plane, options) {
      return SurfaceLook.material(base, { layers: { mirror: { ...options, type: 'planarReflection', plane } } });
    }
  };
  K.ripple = { field: RippleField.field, sampleFrame: RippleField.sampleFrame, glsl: RippleField.glsl };
  K.atmosphere = {
    fog: SceneOptics.fog,
    sphere: SceneOptics.sphere,
    box: SceneOptics.box,
    shaft: SceneOptics.shaft,
    field: SceneOptics.field,
    shaped: SceneOptics.shaped,
    cutouts: VolumeCutouts.compile,
    lighting: SceneOptics.lighting,
    occluder: SceneOptics.occluder,
    history: SceneOptics.volumeHistory,
    prepare: SceneOptics.prepareVolumes,
    trace: SceneOptics.trace
  };
})(KIT);
