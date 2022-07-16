import React, { useState } from "react";
import { Autocomplete, Box } from "@mui/material";
import TextField from "@material-ui/core/TextField";
import { tickerOptions, capitalizeFirstLetters } from "./TickerOptions";
import "../../../../Configs/Global";

export default function NavSearchBarAutocomplete(props) {
  return (
    <div>
      <Autocomplete
        disableClearable={true}
        id="navSearch"
        clearOnEscape={true}
        autoSelect={true}
        options={tickerOptions}
        // options={tickerOptions.sort(
        //   (a, b) => -b.ticker[0].localeCompare(a.ticker[0])
        // )}
        // groupBy={(option) => option.ticker[0].toUpperCase()}
        getOptionLabel={(option) => option.title + " - " + option.ticker}
        onChange={(event, newOption) => {
          props.setSearchQuery(newOption.ticker);
        }}
        renderOption={(props, option) => (
          <Box
            {...props}
            component="li"
            sx={{
              backgroundColor:
                global.config.theme === "dark"
                  ? global.config.darkBG
                  : global.config.lightBG,
              color: global.config.theme === "dark" ? "white" : "black",
            }}
          >
            {capitalizeFirstLetters(option.title)} - {option.ticker}
          </Box>
        )}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Search Stocks..."
            inputProps={{
              ...params.inputProps,
              autoComplete: "off", // disable autocomplete and autofill
            }}
            style={{ width: "100%" }}
          />
        )}
      />
    </div>
  );
}
