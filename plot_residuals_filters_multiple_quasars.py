from __future__ import division
import numpy as np
import matplotlib.pyplot as pp
import pyregion
from mpl_toolkits.axes_grid1 import ImageGrid
from matplotlib.transforms import Affine2D
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import gaussian_filter

from astropy.visualization import AsinhStretch
from astropy.visualization.mpl_normalize import ImageNormalize
from matplotlib import rc
rc('font', family='serif')

_psfresid_pat = 'runJWST/SDSS_z7_{}/mcmc_out_mock_{}_point_source_subtracted.fits'
_psfresid_pat_F200W = 'runJWST/SDSS_z7_SN/mcmc_out_mock_{}_point_source_subtracted.fits'
_true_pat = 'data/sci_mock_JWST_{}_{}_onlyHost.fits'
_mag_zp = 25.9463

_stretch = AsinhStretch()
#_stretch.a = (0.01 - 0.0001)/2 / (0.01+0.0001)
#_pnorm = ImageNormalize(vmin=-0.0001, vmax=0.01, stretch=_stretch, clip=True)
#_xytix = [-3,-2, -1, 0, 1, 2,3]  # in arcsec
_xytix = [-0.3, 0, 0.3]  # in arcsec
_coltix = np.array([26,27,28])  # in mag/arcsec**2
xy_format = pp.FormatStrFormatter(r'$%0.1f^{\prime\prime}$')
_axis_range = [-0.3,0.3,-0.3,0.3]#[-2.5, 2.5, -2.5, 2.5]  # in arcsec

gray_r = pp.cm.cmap_d['Spectral_r']


def mag_to_flux(mag, zp=0.0, scale=(1.0, 1.0)):
    return 10**(-0.4*(mag - zp)) * np.prod(scale)


def plot_models(quasar, filt, save_name=None):
    q_ind = quasar.split('_',1)[1]#+'_host'
    if filt=='F200W':
      psfresid = fits.getdata(_psfresid_pat_F200W.format(quasar))
    else:
      psfresid = fits.getdata(_psfresid_pat.format(filt,quasar))
    trueHost = fits.getdata(_true_pat.format(filt,q_ind))
    #quasardata = fits.getdata(_quasar_pat.format(qdir))

    #cent=int(len(quasardata)/2)
    #flux_ratio=psfresid[cent,cent]/quasardata[cent,cent]
    #print('Flux ratio: ',psfresid[95,95]/quasar[95,95])
    #if flux_ratio>0.05:
    #  print(flux_ratio,quasar)
   
   
    #psfresid_smooth = gaussian_filter(psfresid, (2, 2))
    resid_smooth = gaussian_filter(psfresid, (1, 1))
    true_smooth = gaussian_filter(trueHost, (1, 1))

    center = np.array(psfresid.shape)[::-1]/2
    if filt in ['F277W','F356W','F444W']:
      pxscale = 0.063/2 #arcsec
      #_stretch.a = (0.03 - 0.00001)/2 / (0.03+0.00001)
      #_pnorm = ImageNormalize(vmin=-0.00001*2.4, vmax=0.03*2.4, stretch=_stretch, clip=True)
      _stretch.a = (0.05 - 0.00005)/2 / (0.05+0.00005)
      _pnorm = ImageNormalize(vmin=-0.00005, vmax=0.05, stretch=_stretch, clip=True)
    else:
      pxscale = 0.031/2
      _stretch.a = (0.005 - 0.00005)/2 / (0.005+0.00005)
      _pnorm = ImageNormalize(vmin=-0.00005, vmax=0.005, stretch=_stretch, clip=True)
    extents = np.array([-center[0], center[0],
               -center[1], center[1]])*pxscale

    for ind,data in enumerate([resid_smooth,true_smooth]):
    #for ind,data in enumerate([psfresid,trueHost]):
      if ind==0:
        grid_ind=ii+(2*len(filters)*nn)
        if nn==0:
          grid[grid_ind].set_title(filt)
      else:
        grid_ind=ii+len(filters)+(2*len(filters)*nn)
      im = grid[grid_ind].imshow(data, extent=extents, origin='lower',
                               cmap=gray_r, norm=_pnorm,
                               interpolation='nearest')
      grid[grid_ind].axis(_axis_range)
    
      ticks = mag_to_flux(_coltix, zp=_mag_zp, scale=pxscale)
      cbar = pp.colorbar(im, cax=grid.cbar_axes[0], ticks=ticks)
      grid[grid_ind].set_xticks(_xytix)
      grid[grid_ind].set_yticks(_xytix)
      grid[grid_ind].xaxis.set_major_formatter(xy_format)
      grid[grid_ind].yaxis.set_major_formatter(xy_format)
    cbar.set_ticklabels(_coltix)
    grid.cbar_axes[0].set_ylabel('mag arcsec$^{-2}$')
    grid.cbar_axes[0].set_xlabel('mag arcsec$^{-2}$')

    #grid[ii].set_title(quasar)


if __name__ == '__main__':
    from sys import argv
    # import glob
    to_plot = [2,   3,   6,   7,   8,   9]#  10,  12,  16, 18,  20,  22,  23,  25,  27,  32,  36,  40,  43,  45,  46, 100]
    to_plot = [10,  12,  16, 18,  20]#22,  23,  25,  27,  32,  36,  40,  43,  45,  46, 100]
    filters = ['F115W','F150W','F200W','F277W','F356W','F444W']

    if 'test' in argv:
        to_plot = to_plot[0:1]

    fig = pp.figure(figsize=(7, 10))
    grid = ImageGrid(fig, 111, nrows_ncols=(2*len(to_plot),len(filters)), axes_pad=0.1,
                     label_mode='L',share_all=False,
                     cbar_location='right', cbar_mode='single')

    for nn,qq in enumerate(to_plot):
      ii=0 
      quasar = 'JWST_SDSS_' + str(qq)
      for filt in filters:
        save_name = 'output_image_{}.pdf'.format(quasar) if 'save' in argv else None
        plot_models(quasar, filt, save_name=save_name)
        ii+=1
   
    for ii in range(0,len(to_plot)):
      grid[0+(2*len(filters)*ii)].set_ylabel('Subtracted')
      grid[0+len(filters)+(2*len(filters)*ii)].set_ylabel('True')
    pp.subplots_adjust(left=0.08, bottom=0.1, right=0.92, top=0.95)
    pp.savefig('residuals_filter_comparison_multiple_filters.pdf'.format(qq))
    pp.show() 
    #pp.close(fig)
