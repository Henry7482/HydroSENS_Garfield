// Custom type declarations for modules without official types

declare module 'georaster' {
  export default class GeoRaster {
    constructor(data: any);
    static parseGeoraster(buffer: ArrayBuffer): Promise<GeoRaster>;
    xmin: number;
    xmax: number;
    ymin: number;
    ymax: number;
    width: number;
    height: number;
    values: number[][];
    projection: string;
    _data: any;
  }
}

declare module 'georaster-layer-for-leaflet' {
  import { LayerOptions } from 'leaflet';
  
  export default class GeoRasterLayer {
    constructor(options: {
      georaster: any;
      opacity?: number;
      pixelValuesToColorFn?: (values: number[]) => string;
      resolution?: number;
      debugLevel?: number;
      [key: string]: any;
    } & LayerOptions);
    
    addTo(map: any): this;
    remove(): this;
    setOpacity(opacity: number): this;
  }
}

declare module '@mapbox/shp-write' {
  export interface DownloadOptions {
    filename?: string;
    folder?: string;
    outputType?: string;
  }
  
  export interface ZipOptions {
    compression?: 'DEFLATE' | 'STORE';
    types?: {
      polygon?: string;
    };
    prj?: string;
  }
  
  export function download(
    data: any,
    options?: DownloadOptions & ZipOptions
  ): Blob;
  
  export function zip(
    data: any,
    options?: ZipOptions
  ): Blob;
}

declare module 'geoblaze' {
  export function identify(georaster: any, point: [number, number]): Promise<number[]>;
  export function sum(georaster: any, geometry?: any): Promise<number>;
  export function mean(georaster: any, geometry?: any): Promise<number>;
  export function min(georaster: any, geometry?: any): Promise<number>;
  export function max(georaster: any, geometry?: any): Promise<number>;
}
