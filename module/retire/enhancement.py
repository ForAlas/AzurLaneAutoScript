import numpy as np

from module.base.timer import Timer
from module.base.utils import color_bar_percentage
from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.retire.assets import *
from module.retire.dock import Dock, CARD_GRIDS


class Enhancement(Dock):
    @property
    def _retire_amount(self):
        if self.config.RETIRE_AMOUNT == 'all':
            return 2000
        if self.config.RETIRE_AMOUNT == '10':
            return 10
        return 10

    def _enhance_enter(self, favourite=False, ship_type=None):
        """
        Pages:
            in: page_dock
            out: page_ship_enhance

        Returns:
            bool: False with filter applied resulting
                  in empty dock.
                  Otherwise true with at least 1 card
                  available to be picked.
        """
        if favourite:
            self.dock_favourite_set(enable=True)

        self.dock_filter_enter()
        self.dock_filter_set(category='extra', type='no_limit', enable=True)
        self.dock_filter_set(category='extra', type='enhanceable', enable=True)
        self.dock_filter_set(category='index', type='all', enable=True)
        self.dock_filter_set(category='sort', type='lvl', enable=True)
        self.dock_filter_set(category='faction', type='all', enable=True)
        self.dock_filter_set(category='rarity', type='all', enable=True)
        if ship_type is not None:
            ship_type = str(ship_type)
            self.dock_filter_set(category='index', type=ship_type, enable=True)
        self.dock_filter_confirm()

        if self.appear(DOCK_EMPTY, offset=(30, 30)):
            return False

        self.equip_enter(CARD_GRIDS[(0, 0)], check_button=SHIP_DETAIL_CHECK, long_click=False)
        return True

    def _enhance_quit(self):
        """
        Pages:
            in: page_ship_enhance
            out: page_dock
        """
        self.ui_back(DOCK_FILTER)
        self.dock_favourite_set(enable=False)
        self.dock_filter_enter()
        self.dock_filter_set(category='extra', type='no_limit', enable=True)
        self.dock_filter_set(category='index', type='all', enable=True)
        self.dock_filter_confirm()

    def _enhance_confirm(self):
        """
        Pages:
            in: EQUIP_CONFIRM
            out: page_ship_enhance, without info_bar
        """
        executed = False
        while 1:
            self.device.screenshot()

            # if self.appear_then_click(ENHANCE_CONFIRM, offset=(30, 30), interval=3):
            #     continue
            if self.appear_then_click(EQUIP_CONFIRM, offset=(30, 30), interval=3):
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=(30, 30), interval=3):
                continue
            if self.appear(GET_ITEMS_1, interval=2):
                self.device.click(GET_ITEMS_1_RETIREMENT_SAVE)
                self.interval_reset(ENHANCE_CONFIRM)
                executed = True
                continue

            # End
            if executed and self.appear(ENHANCE_CONFIRM, offset=(30, 30)):
                self.ensure_no_info_bar()
                break

    def _enhance_choose(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_ship_enhance, without info_bar
            out: EQUIP_CONFIRM
        """
        end_activate_timer = Timer(2, count=2) if self.config.DEVICE_CONTROL_METHOD == 'minitouch' else Timer(2, count=1)
        trapped_timer = Timer(15, count=3).start()
        trapped = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                return True

            if not end_activate_timer.reached_and_reset():
                continue

            ensured = self.equip_sidebar_ensure(index=4)
            if ensured:
                self.wait_until_appear(ENHANCE_RECOMMEND, offset=(5, 5), skip_first_screenshot=True)
            else:
                continue

            status = color_bar_percentage(self.device.image, area=ENHANCE_RELOAD.area, prev_color=(231, 178, 74))
            logger.attr('Reload_enhanced', f'{int(status * 100)}%')
            choose = np.sum(np.array(self.device.image.crop(ENHANCE_FILLED.area)) > 200) > 100

            if trapped or self.info_bar_count():
                if status > 0.98:
                    logger.info('Fully enhanced for this ship')
                    swiped = self.equip_view_next(check_button=ENHANCE_RECOMMEND)
                    self.ensure_no_info_bar()
                    if not swiped:
                        return False
                    trapped_timer.reset()
                    trapped = False
                    continue
                else:
                    if choose:
                        logger.info('Unable to enhance this ship')
                        swiped = self.equip_view_next(check_button=ENHANCE_RECOMMEND)
                        self.ensure_no_info_bar()
                        if not swiped:
                            return False
                        trapped_timer.reset()
                        trapped = False
                        continue
                    else:
                        logger.info('Enhancement material exhausted')
                        return False

            if not trapped_timer.reached_and_reset() and self.appear_then_click(ENHANCE_RECOMMEND, offset=(5, 5), interval=2):
                self.device.sleep(0.3)
                self.device.click(ENHANCE_CONFIRM)
            else:
                logger.warning('Current status appears trapped, will force stat gauge check')
                trapped = True

    def _enhance_choose_simple(self, current_index=0, skip_first_screenshot=True):
        """
        Description:
            Simplified _enhance_choose focuses only on
            appearance of info_bars, stat gauge is ignored
            Minimum 2 times before swiping, if maximum of
            4 times is detected, a forced swipe is initiated
            A maximum of 4 ships will be checked to account
            for 'in battle' status, hard-coded otherwise if
            desired can be configurable

        Pages:
            in: page_ship_enhance, without info_bar
            out: EQUIP_CONFIRM
        """
        end_activate_timer = Timer(2, count=2) if self.config.DEVICE_CONTROL_METHOD == 'minitouch' else Timer(2, count=1)
        next_timer = Timer(2, count=1).start()
        trapped_timer = Timer(15, count=3).start()
        trapped = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                return True, current_index

            if not end_activate_timer.reached_and_reset():
                continue

            ensured = self.equip_sidebar_ensure(index=4)
            if ensured:
                self.wait_until_appear(ENHANCE_RECOMMEND, offset=(5, 5), skip_first_screenshot=True)
            else:
                continue

            if trapped or self.info_bar_count():
                if trapped or next_timer.reached():
                    logger.info('Unable to enhance this ship, swipe to next')
                    swiped = self.equip_view_next(check_button=ENHANCE_RECOMMEND)
                    self.ensure_no_info_bar()
                    if not swiped or current_index >= 3:
                        logger.info('Cannot swipe or ship check threshold reached, exiting current category')
                        return False, current_index
                    else:
                        next_timer.reset()
                        trapped_timer.reset()
                        trapped = False
                        logger.info(f'Try next ship: {3 - current_index}/3 remaining until give up')
                        current_index += 1
                        continue

            if not trapped_timer.reached_and_reset() and self.appear_then_click(ENHANCE_RECOMMEND, offset=(5, 5), interval=2):
                self.device.sleep(0.3)
                self.device.click(ENHANCE_CONFIRM)
            else:
                logger.warning('Current status appears trapped, will force swipe to next ship')
                trapped = True

    def enhance_ships(self, favourite=None):
        """
        Pages:
            in: page_dock
            out: page_dock

        Args:
            favourite (bool):

        Returns:
            int: total enhanced
        """
        if favourite is None:
            favourite = self.config.ENHANCE_FAVOURITE

        logger.hr('Enhancement')
        logger.info(f'Favourite={favourite}')
        self._enhance_enter(favourite=favourite)
        total = 0

        # At least one card present, able to enhance
        if self._enhance_enter(favourite=favourite):
            while 1:
                if not self._enhance_choose():
                    break
                self._enhance_confirm()
                total += 10
                if total >= self._retire_amount:
                    break

        self._enhance_quit()
        return total

    def enhance_ships_order(self, favourite=None):
        """
        Info:
            Target ships in order of specified
            type listing by ENHANCE_ORDER_STRING

        Pages:
            in: page_dock
            out: page_dock

        Args:
            favourite (bool):

        Returns:
            int: total enhanced
        """
        if favourite is None:
            favourite = self.config.ENHANCE_FAVOURITE

        logger.hr('Enhancement by type')
        total = 0

        ship_types = [s.strip().lower() for s in self.config.ENHANCE_ORDER_STRING.split('>')]
        enable_simple = True
        if ship_types == ['']:
            enable_simple = False
            ship_types = [None]
        logger.attr('Enhance Order', ship_types)

        for ship_type in ship_types:
            index = 0 # Helper variable only for _enhance_choose_simple
            logger.info(f'Favourite={favourite}, Ship Type={ship_type}')
            if not self._enhance_enter(favourite=favourite, ship_type=ship_type):
                logger.hr(f'Dock Empty by ship type {ship_type}')
                continue

            while 1:
                if enable_simple:
                    choose_result, index = self._enhance_choose_simple(current_index=index)
                else:
                    choose_result = self._enhance_choose()
                if not choose_result:
                    break
                self._enhance_confirm()
                total += 10
                if total >= self._retire_amount:
                    break
            self.ui_back(DOCK_FILTER)

        self._enhance_quit()
        return total

    def _enhance_handler(self):
        """
        Pages:
            in: RETIRE_APPEAR
            out:

        Returns:
            int: enhance turn count
        """
        self.ui_click(RETIRE_APPEAR_3, check_button=DOCK_FILTER, skip_first_screenshot=True)
        self.handle_dock_cards_loading()

        total = self.enhance_ships_order()

        self.dock_quit()
        self.config.DOCK_FULL_TRIGGERED = True

        return total
