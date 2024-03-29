import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from photutils import CircularAperture,CircularAnnulus
from photutils import aperture_photometry, background
from matplotlib.colors import SymLogNorm
import sys
import pandas as pd

def flux_to_mag(flux):
    return -2.5*np.log10(flux/(3631e9)) #flux in nJy

def full_mag(counts):
    return -2.5*np.log10(np.sum(counts))+25.9463


def ap_phot(counts):
    cent=[int(len(counts)/2),int(len(counts)/2)]
    zeropoint=25.9463
    ap = (len(counts)/2) #Full sized circular aperture for photometry.
    #ap_counts=np.zeros(20)
    #annulus_aperture = CircularAnnulus(cent, r_in=(len(counts)/2)*0.95, r_out=(len(counts)/2))
    #for ii,ap in enumerate(ap*np.linspace(0.05,1,20)):
    for ap in [ap]:#enumerate(np.linspace(1,35,10)):#[30]: Tested, brightness profiles flatten by r=25 (For 35 length array).
      aperture = CircularAperture(cent, r=ap)
      #apers = [aperture, annulus_aperture]

      phot_table = aperture_photometry(counts, aperture)
      ###No background level in mock images, don't need sky subtraction
      #bkg_mean = phot_table['aperture_sum_1'] / annulus_aperture.area
      #bkg_sum = bkg_mean * aperture.area
      ap_counts = phot_table['aperture_sum'] #- bkg_sum #Sky subtraction
      #print(bkg_sum,bkg_sum/phot_table['aperture_sum_0']) ##Bkg ~2% of total flux

      mag=-2.5*np.log10(ap_counts[0])+zeropoint
      #mag=-2.5*np.log10(ap_counts[ii])+zeropoint
      #print('Photometric measurement: {:04.2f}'.format(mag))
    
    
    #fig,ax=plt.subplots()
    #im=ax.imshow((counts),norm=SymLogNorm(1e-7,vmin=np.amin(counts),vmax=np.amax(counts)))#norm=SymLogNorm(0.01,vmin=-0.2,vmax=0.2))#cmap='inferno',vmin=0,vmax=0.02)
    #annulus_masks = aperture.to_mask(method='center')
    #annulus_data = annulus_masks.multiply(counts)

    #circle2=plt.Circle(cent,ap, fill=False,color='k',linestyle='--')
    #ax.add_artist(circle2)
    #plt.show()
 
    #plt.plot(np.linspace(0.05,1,20),ap_counts) 
    #plt.axhline(np.sum(counts))
    #plt.axhline(0.99*np.sum(counts))
    #plt.ylim(0,np.sum(counts))
    #plt.show()
    return mag


if __name__=='__main__':
  indices=np.array([2,3,6,7,8,9,10,12,16,18,20,22,23,25,27,32,36,40,41,43,45,46,100])
  host_mag={'input':np.zeros(len(indices)-1),'psfMC':np.zeros(len(indices)-1),'phot':np.zeros(len(indices)-1),
            'diff_phot':np.zeros(len(indices)-1),'phot_true':np.zeros(len(indices)-1)}
  AGN_mag={'input':np.zeros(len(indices)-1),'psfMC':np.zeros(len(indices)-1),'phot':np.zeros(len(indices)-1),
            'diff_phot':np.zeros(len(indices)-1),'full_array':np.zeros(len(indices)-1),'no_noise':np.zeros(len(indices)-1)}

  filt_no={'F115W':0,'F150W':1,'F200W':2,'F277W':3,'F356W':4,'F444W':5,'F560W':6,'F770W':7}
 
  for filt in ['F115W','F150W','F200W','F277W','F356W','F444W','F560W','F770W']:
    print('______________________________'+filt+'________________________________')
    #filt='F115W'

    host_flux=np.load('host_flux.npy')[filt_no[filt]]
    AGN_flux=np.load('AGN_flux.npy')[filt_no[filt]] #2 = F200W

    for ii,ind in enumerate(indices):
      if ind>41:
        ii-=1
      if ind!=41:
        #load images and flux values
        #ind=str(sys.argv[1])
        title='SDSS_'+str(ind)
        loc=np.where(indices==int(ind))[0][0]

        host_mag['input'][ii] = flux_to_mag(host_flux[loc])
        AGN_mag['input'][ii] = flux_to_mag(AGN_flux[loc])

        #####Test host magnitude
        #counts = fits.getdata('mcmc_out_mock_HST_convolved_model.fits')
        if filt=='F200W':
          head = fits.getheader('runJWST/SDSS_z7_SN/mcmc_out_mock_JWST_'+title+'_residual.fits')
        else:
          head = fits.getheader('runJWST/SDSS_z7_'+filt+'/mcmc_out_mock_JWST_'+title+'_residual.fits')
        host_mag['psfMC'][ii]=float(head['2SER_MAG'].split(' ')[0])
        #print('Host subtraction fit: ',head['2SER_MAG'])
        #print('Host input mag: ',host_mag)
  
        if filt=='F200W':
          counts = fits.getdata('runJWST/SDSS_z7_SN/mcmc_out_mock_JWST_'+title+'_point_source_subtracted.fits')
        else:
          counts = fits.getdata('runJWST/SDSS_z7_'+filt+'/mcmc_out_mock_JWST_'+title+'_point_source_subtracted.fits')
 
        #counts = fits.getdata('data/sci_mock_HST_f160w_'+title+'_onlyHost.fits')
        host_mag['phot'][ii]=ap_phot(counts) 
        host_mag['diff_phot'][ii]=host_mag['phot'][ii]-host_mag['input'][ii]
   
        counts = fits.getdata('data/sci_mock_JWST_'+filt+'_'+title+'_onlyHost.fits')
        host_mag['phot_true'][ii]=ap_phot(counts) 
 
        #####Test quasar magnitude
        #print('______________________________________________')
        #print('Quasar: Host subtraction fit: ',head['1PS_MAG'])
        AGN_mag['psfMC'][ii]=float(head['1PS_MAG'].split(' ')[0])
        #print('Quasar: input mag: ',AGN_mag)
        counts = fits.getdata('data/sci_mock_JWST_'+filt+'_'+title+'.fits')
        AGN_mag['phot'][ii]=ap_phot(counts)
        AGN_mag['diff_phot'][ii]=AGN_mag['phot'][ii]-AGN_mag['input'][ii]
      
      counts = fits.getdata('data/sci_mock_JWST_'+filt+'_'+title+'_noNoise.fits') #Image with no background
      #AGN_mag['no_noise'][ii]=ap_phot(counts)
      #AGN_mag['full_array'][ii]=full_mag(counts) ###


    print('_________ AGN _________')
    #print('Measured - No Noise')
    #print(np.mean(AGN_mag['phot']-AGN_mag['no_noise']))
    print('Measured - Input')
    x=AGN_mag['diff_phot']
    #print(np.mean(x),np.std(x),np.min(x),np.max(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    print(np.mean(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    #print('Measured - full array')
    #print(np.mean(AGN_mag['phot']-AGN_mag['full_array']))
    print('Measured - psfMC')
    x=AGN_mag['phot']-AGN_mag['psfMC']
    #print(np.mean(x),np.std(x),np.min(x),np.max(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    print(np.mean(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    #print('No noise - psfMC')
    #print(np.mean(AGN_mag['no_noise']-AGN_mag['psfMC']))
    print('psfMC - Input')
    x=AGN_mag['psfMC']-AGN_mag['input']
    print(np.mean(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    #print('Full Array - Input')
    #print(np.mean(AGN_mag['full_array']-AGN_mag['input']))
    #print('Full array - psfMC')
    #print(np.mean(AGN_mag['full_array']-AGN_mag['psfMC']))
 
 
    print('_________ Host _________')
    print('Measured (subtracted) - Measured (true)')
    x=(host_mag['phot']-host_mag['phot_true'])
    print(np.mean(x),np.std(x),np.min(x),np.max(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    print('Measured - Input')
    x=(host_mag['diff_phot'])
    print(np.mean(x),np.std(x),np.min(x),np.max(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    print('Measured - psfMC')
    x=host_mag['phot']-host_mag['psfMC']
    print(np.mean(x),np.std(x),np.min(x),np.max(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
    print('psfMC - Input')
    x=host_mag['psfMC']-host_mag['input']
    print(np.mean(x),np.std(x),np.min(x),np.max(x),10**(-0.4*np.min(x)),10**(-0.4*np.max(x)))
