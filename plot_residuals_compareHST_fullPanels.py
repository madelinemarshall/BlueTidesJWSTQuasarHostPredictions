from __future__ import division
import numpy as np
import matplotlib.pyplot as pp
import pyregion
from mpl_toolkits.axes_grid1 import ImageGrid
from matplotlib.transforms import Affine2D
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import gaussian_filter

from astropy.visualization import AsinhStretch, LogStretch
from astropy.visualization.mpl_normalize import ImageNormalize
from matplotlib import rc
rc('font', family='serif')
rc('font',size = (9))

_psfresid_pat_H = 'runHST/SDSS_z7/mcmc_out_mock_{}_point_source_subtracted.fits'
_psfresid_pat_J = 'runJWST/SDSS_z7_F150W_4800s/mcmc_out_mock_{}_point_source_subtracted.fits'
#_psfresid_pat = 'data/ivm_mock_{}_host_SN.fits'
_mag_zp = {'F125W': 26.2303, 'F160W': 25.9463}

_stretch = AsinhStretch()
_stretch.a = (0.01 - 0.0001)/2 / (0.01+0.0001)
_axis_range = [-0.7,0.7,-0.7,0.7]#[-2.5, 2.5, -2.5, 2.5]  # in arcsec
#_xytix = [-3,-2, -1, 0, 1, 2,3]  # in arcsec
_xytix = [-0.5, 0, 0.5]  # in arcsec

gray_r = pp.cm.cmap_d['Spectral_r']

def pad_and_rfft_image(img, newshape):
    """
    Pads the psf array to the size described by imgshape, then run rfft to put
    it in Fourier space.
    """
    # TODO: pad with white noise instead of zeros?
    pad = np.asarray(newshape) - np.asarray(img.shape)
    if np.any(pad < 0):
        raise NotImplementedError('PSF images larger than observation images '
                                  'are not yet supported')
    img_pad = np.zeros(newshape, dtype=img.dtype)
    img_pad[pad[0]//2:pad[0]//2 + img.shape[0],
            pad[1]//2:pad[1]//2 + img.shape[1]] = img
    return np.fft.rfft2(img_pad)


def norm_psf(psf_data):
    """
    Returns normed psf and correspondingly scaled IVM.
    Uses math.fsum for its stable summation algorithm
    """
    psf_sum = np.sum(psf_data.flat)
    return psf_data / psf_sum


def make_convolved(raw_model,psf):
    fourier_kernel=pad_and_rfft_image(norm_psf(psf),np.shape(raw_model))
    maxloc=(np.unravel_index(np.argmax(raw_model),np.array(raw_model).shape))[0]
    raw_model[maxloc,maxloc]=(raw_model[maxloc,maxloc-1]+raw_model[maxloc,maxloc+1])/2 #remove quasar
    return np.fft.ifftshift(np.fft.irfft2(np.fft.rfft2(raw_model) * fourier_kernel))


def mag_to_flux(mag, zp=0.0, scale=(1.0, 1.0)):
    return 10**(-0.4*(mag - zp)) * np.prod(scale)


def plot_models(quasar, save_name=None):
    if HST:
      _quasar_pat = 'data/sci_mock_{}_onlyHost.fits'
      quasar = 'HST_SDSS_' + str(quasar)
      qdir = 'HST_f160w_'+quasar.split('_',1)[1]#+'_host'
      psf = fits.open('data/sci_PSF_HST_f160w_SN.fits')[0].data
      pxscale = 0.13/2 #arcsec
      _psfresid_pat=_psfresid_pat_H
      area_fact=1#0.0569
      ttle='HST'
      mark=r'$\times$'
      mark_col='red'
      _pnorm = ImageNormalize(vmin=-0.00005, vmax=0.05, stretch=_stretch, clip=True)
      _coltix = np.array([27,28,29])  # in mag/arcsec**2
    
    else:
      _quasar_pat = 'data/sci_mock_{}_onlyHost_4800s.fits'
      quasar = 'JWST_SDSS_' + str(quasar)
      qdir = 'JWST_F150W_'+quasar.split('_',1)[1]#+'_host'
      psf = fits.open('data/sci_PSF_JWST_F150W_SN_4800s.fits')[0].data
      pxscale = 0.031/2
      _psfresid_pat=_psfresid_pat_J
      area_fact=1
      ttle='JWST'
      mark=r'$\checkmark$'
      mark_col='limegreen'
      _pnorm = ImageNormalize(vmin=-0.00005, vmax=0.01, stretch=_stretch, clip=True)
      _coltix = np.array([27,28,29])  # in mag/arcsec**2

    if trueImage:
      ttle='True Host'
      psfresid = fits.getdata(_quasar_pat.format(qdir))
    elif convolved: 
      raw_model = fits.open(_psfresid_pat.format(quasar)[:-28]+'raw_model.fits')[0].data
      convolved_model = make_convolved(raw_model,psf)
      ttle='Sersic Model'
      psfresid = convolved_model#fits.getdata(_psfresid_pat.format(quasar))
    elif residual:
      ttle='Residual'
      psfresid = fits.open(_psfresid_pat.format(quasar)[:-28]+'residual.fits')[0].data
    else:
      ttle='PSF-Subtracted'
      psfresid = fits.getdata(_psfresid_pat.format(quasar))
   
    filt = 'F160W'
    #psfresid_smooth = gaussian_filter(psfresid, (2, 2))
    psfresid_smooth = gaussian_filter(psfresid, (1, 1))

    center = np.array(psfresid.shape)[::-1]/2
    
    extents = np.array([-center[0], center[0],
               -center[1], center[1]])*pxscale

    #plot_panels = [psfresid, 'Point Source\nSubtracted']
    plot_panels = [psfresid_smooth, 'Point Source\nSubtracted']
    flx = plot_panels[0]*area_fact #puts HST on the same vertical scale (bigger pixels -> volume different).

    im = grid[ii].imshow(flx, extent=extents,
                               origin='lower',
                               cmap=gray_r, norm=_pnorm,
                               interpolation='nearest')
    grid[ii].axis(_axis_range)
    
    ticks = mag_to_flux(_coltix, zp=_mag_zp[filt], scale=pxscale)
    if HST:
      cbar = pp.colorbar(im, cax=grid.cbar_axes[0], ticks=ticks)
      cbar.set_ticklabels(_coltix)
      grid.cbar_axes[0].set_ylabel('mag arcsec$^{-2}$')
      grid.cbar_axes[0].set_xlabel('mag arcsec$^{-2}$')
    else:
      cbar = pp.colorbar(im, cax=grid.cbar_axes[1], ticks=ticks)
      cbar.set_ticklabels(_coltix)
      grid.cbar_axes[1].set_ylabel('mag arcsec$^{-2}$')
      grid.cbar_axes[1].set_xlabel('mag arcsec$^{-2}$')
    if ii<4:
       grid[ii].set_title(ttle)#,fontsize=10)
    if convolved:
       grid[ii].text(0.35,-0.55,mark,color=mark_col,fontsize=20)
    #grid[ii].set_title(quasar)

if __name__ == '__main__':
    from sys import argv
    # import glob
    to_plot = [2,   3,   6,   7,   8,   9,  10,  12,  16, 18,  20,  22,  23,  25,  27,  32,  36,  40,  43,  45,  46, 100]
    ##Detection for: [3  6  7 10 12 16 25 32 36 43]
    to_plot = [43]#12]#,43]

    if 'test' in argv:
        to_plot = to_plot[0:1]

    fig = pp.figure(figsize=(8, 3))
    grid = ImageGrid(fig, 111, nrows_ncols=(len(to_plot)*2,4), axes_pad=0.1,
                     share_all=True, label_mode='L',
                     cbar_location='right', cbar_mode='edge')
    jj=0 
    ii=0
    for quasar in to_plot:
        save_name = 'output_image_{}.pdf'.format(quasar) if 'save' in argv else None
        trueImage=0
        convolved=0
        residual=0
        ###HST
        HST=1
        #ii=jj
        plot_models(quasar, save_name=save_name)
        ii+=1
        convolved=1
        plot_models(quasar, save_name=save_name)
        ii+=1
        convolved=0
        residual=1
        plot_models(quasar, save_name=save_name)
        ii+=1
        residual=0
        trueImage=1
        #ii=jj+len(to_plot)
        plot_models(quasar, save_name=save_name) 
        ii+=1
        
        ###JWST
        HST=0
        trueImage=0
        #ii=jj+2*len(to_plot)
        plot_models(quasar, save_name=save_name) 
        ii+=1
        convolved=1
        plot_models(quasar, save_name=save_name)
        ii+=1
        convolved=0
        residual=1
        plot_models(quasar, save_name=save_name)
        ii+=1
        residual=0
        trueImage=1
        #ii=jj+3*len(to_plot)
        plot_models(quasar, save_name=save_name) 
        ii+=1
        #jj+=1"""

    grid[0].set_ylabel('HST')
    grid[4].set_ylabel('JWST')


    xy_format = pp.FormatStrFormatter(r'$%0.1f^{\prime\prime}$')
    for ax in grid:
        ax.set_xticks(_xytix)
        ax.set_yticks(_xytix)
        ax.xaxis.set_major_formatter(xy_format)
        ax.yaxis.set_major_formatter(xy_format)
    pp.subplots_adjust(left=0.1, bottom=0.1, right=0.92, top=0.92)
    pp.savefig('residual_HSTvsJWST_fullPanels_2.pdf')
    pp.show()
    pp.close(fig)
