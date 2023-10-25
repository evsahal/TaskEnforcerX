#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

get_all_boss_monster_info_query = """select boss_monster.id,boss_monster.preview_name,boss_monster.monster_title, 
boss_monster.monster_category,boss_monster.system,boss_monster.enable_map_scan,boss_monster.monster_logic_id,monster_level_info.id,
monster_level_info.level,monster_level_info.name, monster_level_info.size, monster_image.preview_image, 
monster_image.img_540p,monster_image.img_threshold, monster_image.click_pos,boss_monster.monster_image_id 
from boss_monster, monster_level_info,monster_image where boss_monster.monster_image_id = monster_image.id and 
boss_monster.id = monster_level_info.boss_monster_id """

get_all_normal_monster_info_query = """select normal_monster.id,normal_monster.monster_name,normal_monster.system, 
monster_image.preview_image,monster_image.img_540p, monster_image.img_threshold,
monster_image.click_pos,monster_image.id from normal_monster, monster_image where normal_monster.monster_image_id = 
monster_image.id"""

get_all_scoutables_info_query = """select scoutables.id,scoutables.scoutables_name,scoutables.type,scoutables.system, 
monster_image.preview_image,monster_image.img_540p, monster_image.id from scoutables,
monster_image where scoutables.monster_image_id = monster_image.id """

get_all_profiles_info_query = """ select * from profile """

get_all_collective_info_query = """select * from collective"""

check_boss_collective_item_query = """select collective.id from collective where collective.coordinates = :cords and 
collective.boss_monster_id = :b_id"""

check_monster_collective_item_query = """select collective.id from collective where collective.coordinates = :cords and 
collective.normal_monster_id = :m_id"""

check_scoutables_collective_item_query = """select collective.id from collective where collective.coordinates = :cords and 
collective.scoutables_id = :s_id"""


add_collective_query = """insert into collective(type,boss_monster_id,normal_monster_id,scoutables_id,coordinates,
show_scan,expires_at) values(:type,:b_id,:m_id,:s_id,:cords, :show_scan, :expires_at)"""

add_profile_query = "insert into profile(profile_name,controls) values(:profile_name,:controls)"

update_profile_query = "Update profile set profile_name = :profile_name,controls = :controls where id = :id"

delete_profile_by_id_query = "delete from profile WHERE id = :id"

update_profile_control_by_name_query = "Update profile set controls = :controls where profile_name = :name"

add_monster_image_query = ("insert into monster_image(preview_image,img_540p,img_threshold,click_pos) values(:p_img,"
                           ":540p,:threshold,:click_pos)")

add_boss_monster_query = "insert into boss_monster(preview_name,monster_title,monster_category,monster_image_id," \
                         "monster_logic_id) values(:p_name,:title,:category,:img_id,:logic_id) "

add_boss_monster_query_upload = "insert into boss_monster(preview_name,monster_title,monster_category," \
                                "monster_image_id,monster_logic_id,system,enable_map_scan) values(:p_name,:title," \
                                ":category,:img_id,:logic_id,:system,:enable_map_scan) "


add_normal_monster_query = "insert into normal_monster(monster_name,monster_image_id,system) values(:m_name,:img_id," \
                           ":system) "

add_scoutables_query = "insert into scoutables(scoutables_name,type,monster_image_id,system) values(:s_name,:type,:img_id," \
                       ":system) "

add_monster_level_query = "insert into monster_level_info(boss_monster_id,level,name,size) values(:boss_monster_id," \
                          ":level,:name,:size)"

get_all_emulator_profiles = "select * from emulator_controls"

update_emulator_port = "Update emulator_controls set emulator_port = :emulator_port where id = :id"

update_emulator_name = "Update emulator_controls set emulator_name = :emulator_name where id = :id"

update_emulator_mode = "Update emulator_controls set emulator_mode = :emulator_mode where id = :id"

update_emulator_profile = "Update emulator_controls set emulator_profile = :emulator_profile where id = :id"

get_troop_tier_info = "select * from troop_tier_info where type = :troop_type and tier = :troop_tier"

get_all_monster_names = "select distinct name from monster_level_info"

get_all_normal_monster_names = "select  monster_name from normal_monster"

get_all_scoutables_names = "select  scoutables_name from scoutables"

get_all_boss_monster_preview_names = "select preview_name from boss_monster"

delete_monster_images_with_id = "delete from monster_image WHERE id = :img_id"

delete_scoutables_with_id = "delete from scoutables WHERE id = :id"

delete_normal_monster_with_id = "delete from normal_monster WHERE id = :id"

delete_boss_monster_with_id = "delete from boss_monster WHERE id = :id"

delete_boss_monster_levels_with_boss_monster_id = "delete from monster_level_info WHERE boss_monster_id = :id"
