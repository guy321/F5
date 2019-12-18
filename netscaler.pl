#!/usr/bin/python3
# Inititial gloal arrays
#fn = "intnetscaler.conf"
fn = "extnetscaler.conf"
m_avs = []          # Add Virtual Server
m_bvs = []          # Bind Virtual Server
m_acs = []          # Add Content Server
m_bcs = []          # Bind Content Server
m_csp = []          # Add Content Server Policy
m_rsp = []          # Add Responder Server Policy
m_asrv = []          # Add server
m_asvcg = []         # Add service group
m_bsvcg = []         # Bind service group
m_amon = []         # Add Monitor 
m_cs_dict = []      # List of Dictionary containing info for irules
m_pool_dict = []

# Function pulls Netscaler conf into lists
def proc_conf ():                    
 vscount = 0
 for line1 in open(fn):
   if "add lb vserver" in line1:
    vscount += 1
    avs = line1.split(' ')
    m_avs.append(avs)
   if "bind lb vserver " in line1:
    bvs = line1.split(' ')
    m_bvs.append(bvs)
   if "add cs vserver " in line1:
    acs = line1.split(' ')
    m_acs.append(acs)
   if "bind cs vserver " in line1:
    bcs = line1.split(' ')
    m_bcs.append(bcs)
   if "add cs policy " in line1:
    csp = line1.split(' ')
    m_csp.append(csp)
   if "add responder policy " in line1:
    rsp = line1.split(' ')
    m_rsp.append(rsp)
   if "add server" in line1:
    asrv = line1.split(' ')
    m_asrv.append(asrv)
   if "add serviceGroup" in line1:
    asvcg = line1.split(' ')
    m_asvcg.append(asvcg)
   if "bind serviceGroup" in line1:
    bsvcg = line1.split(' ')
    m_bsvcg.append(bsvcg)
   if "add lb monitor" in line1:
    amon = line1.split(' ')
    m_amon.append(amon)
# print ( *m_bcs, sep = ' ' + '\r\n')
 return;  


def gen_irule (): 
 zero_lbvs_list = [ a for a in m_avs if "0.0.0.0" in a]          #Search no IP
 zero_lbvs_names = [ z[3] for z in zero_lbvs_list ]                #Extract names  

#  This line evaluates the LBVS with 0.0.0.0 against Bind CS to get cs name then
#  evaluates against cs add to get IP address. Finally, it evaluates against csp
#  to get policy.

 cs_list = [ b[3] +  ' ' +  b[5] + ' ' + bv[4] + ' ' + c[5] + ' ' + b[9] for z in
 zero_lbvs_names for b in m_bcs if z in b for c in m_csp if b[5] == c[3] for bv
 in m_bvs if b[7] == bv[3]]
 cs_list.sort()
# print (cs_list)
# read cs lines into dictionary so the key can be used for refrence in irule
# generation
 
 for c in range(len(cs_list)):
  cs_key = cs_list[c]
  cs_key = cs_key.split(' ')
#  print (cs_key)
  cs_dict = { cs_key[0] : cs_key[1:] for i in range(0, len(cs_key)) } 
  m_cs_dict.append( cs_dict )
# print (*m_cs_dict, sep = ' ' + '\r\n')

#  print ('ltm rule /Common/_vs_filenet_test_HTTPS {') 
 return;

# This fuction takes the srvgrp list and turns into a list of dictionaries
def gen_pools():
 pool_lines = [ a[2] + ' ' + b[3] + ' ' + b[4] for a in m_asvcg for b in m_bsvcg if a[2] == b[2]]
# pool_lines = [p.split(' ') for p in pool_lines] 
 pool_lines.sort()
 for p in range(len(pool_lines)):
  pool_key = pool_lines[p]
  pool_key = pool_key.split(' ')
#  print (pool_key)
  pool_dict = { pool_key[0] : pool_key[1:] for i in range (0, len(pool_key)) }
  m_pool_dict.append( pool_dict )
#  print (m_pool_dict[2]['svcgrp_ad_auth_sslp'])
 return;



# Main function calls
proc_conf ()
gen_irule ()
gen_pools ()

#for key in m_pool_dict[66].keys():
# print (key)

#  This fuction takes a known servicegroup name and outputs all of conf lines
#  in a single list.  The intent is to call this function from a function that
#  produces the tmsh pool creation text.

def get_pool_out( pool_key ):
 pool_out = []
 pool_out.append( pool_key )
 for p in range(0, len(m_pool_dict)):
  if pool_key in m_pool_dict[p]: 
   pool_out.append( m_pool_dict[p][pool_key] )
 return (pool_out);
pool_out = get_pool_out( 'svcgrp_wase_devinti_855')
print ( pool_out )


# Diagnostic
#print ( *m_avs, sep = ' ' + '\r\n')
#print ( *m_bvs, sep = ' ' + '\r\n')
#print ( *m_acs, sep = ' ' + '\r\n')
#print ( *m_bcs, sep = ' ' + '\r\n')
#print ( *m_asrv, sep = ' ' + '\r\n')
#print ( *m_asvcg, sep = ' ' + '\r\n')
#print ( *m_bsvcg, sep = ' ' + '\r\n')
#print ( *m_amon, sep = ' ' + '\r\n')
#print (*m_cs_dict, sep = ' ' + '\r\n')
